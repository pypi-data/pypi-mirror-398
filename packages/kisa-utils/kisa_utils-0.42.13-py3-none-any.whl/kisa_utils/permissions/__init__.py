from typing import Any, get_type_hints, Callable
from copy import deepcopy
from threading import Lock
import inspect
from functools import wraps

from kisa_utils.response import Response, Ok, Error
from kisa_utils.structures.validator import validateWithResponse
from kisa_utils.structures.validator import Value
from kisa_utils import dates
from kisa_utils.db import Handle
from kisa_utils.encryption import decrypt, encrypt
from kisa_utils.storage import encodeJSON, decodeJSON

from . import __config__

class Permissions:

    __dbTableName = 'permissions'
    __dbTables = {
        __dbTableName: '''
            creationTimestamp varchar(25) not null,
            details text not null
        ''',
    }

    # locks used to update properties during write operations
    __locks = {'__global__': Lock()}

    # this dictionary will enable our class to be a singleton. only one object/instance should be used for a single projectId
    __uniqueInstances = {}

    __roleMarker = 'role:'

    @staticmethod
    def getInstance(projectId:str) -> Response:
        '''
        get Permissions instance

        Args:
            projectId(str): project-id of the permissions instance
        '''
        instance = Permissions._Permissions__uniqueInstances.get(projectId, None)
        return Error('no instance found for projectId') if not instance else Ok(instance)
    

    @property 
    def version(self,) -> str:
        '''
        get version of kisa-permissions
        '''
        return '1.0'

    @property
    def id(self) -> str:
        '''get permissions instance Identifier, Id'''
        return self.__id

    @property
    def globalPermissions(self) -> list[str]:
        '''get global permissions'''
        return [permission for permission in self.__globalPermissions]

    @property
    def resources(self) -> dict[str, list[str]]:
        '''get a dict of resources with each resource having its permissions'''
        return {resource: [permission for permission in self.__resources[resource]] for resource in self.__resources}

    @property
    def users(self) -> dict[str, dict[str, dict[str, bool]]]:
        '''
        get users in permissions the users are represented as follows

        ```
        {
            "user1": {
                "resource1": {
                    "permission1": bool,
                    "permission2": bool,
                    ...
                },
                ...
            },
            ...
        }
        ```
        '''
        return {user: deepcopy(self.__users[user]) for user in deepcopy(self.__users) if not user.startswith(self.__roleMarker)}

    @property
    def roles(self) -> dict[str, dict[str, dict[str, bool]]]:
        '''
        get registered roles represented as follows

        ```
        {
            "role1": {
                "resource1": {
                    "permission1": bool,
                    "permission2": bool,
                    ...
                },
                ...
            },
            ...
        }
        ```
        '''
        return {user[len(self.__roleMarker):]: deepcopy(self.__users[user]) for user in deepcopy(self.__users) if user.startswith(self.__roleMarker)}

    @property
    def anyResource(self) -> str:
        '''get the internal representation of resource `any`'''
        return '*'

    @property
    def mainResource(self) -> str:
        '''get the internal representation of resource `main`'''
        return 'main'

    @property
    def anyPermission(self) -> str:
        '''get the internal representation of permission `any`'''
        return '*'

    # make this class a singleton
    def __new__(cls, *args, **kwargs) -> 'Permissions':
        projectId = args[0]
        with Permissions.__locks['__global__']:
            if projectId in Permissions.__uniqueInstances:
                return Permissions.__uniqueInstances[projectId]

        instance = super().__new__(cls)
        Permissions.__uniqueInstances[projectId] = instance
        return instance

    def __init__(self, projectId:str, /, *, dbPath:str=__config__.paths['db']) -> None:
        '''
        create permission instance

        Args:
            projectId(str): permissions object identifier (persists across processes)
            dbPath(str): path to the permissions database
        '''

        if not (response := self.__projectIdValidator(projectId)).status:
            raise ValueError(response.log)

        if not __config__.Path.createDirectory(dbPath)['status']:
            raise ValueError(f'failed to creaet permissions path: {dbPath}')
        
        self.__dbFilePath = f'{dbPath}/{__config__.dbFileName.format(projectId=projectId)}'

        self.__id = projectId
        self.__globalPermissions = {}
        self.__resources = {self.anyResource:{}, self.mainResource:{}}
        self.__users = {}
        self.__lastModified = '1970-01-01 00:00:00'

        with Permissions.__locks['__global__']:
            if self.__id not in Permissions.__locks:
                Permissions.__locks[self.__id] = Lock()

        if not (response:=self.__loadFromDatabase()) and response.log!='no-saved-data':
            import sys
            sys.exit(f'[PANIC] error loading permissions: {response.log}')

    # utils...
    def __getCallStack() -> str:
        '''
        function to get the call stack to help isolate permissions-related errors
        
        Note:
            This function is only visible in the class scope and its NOT a static method
        '''
        callStack = inspect.stack()
        functionCallStack = [s.function for s in callStack if s.function not in ['__perms_decorated_func']]
        functionCallStack.reverse()
        return '::'.join(functionCallStack[:-1]) + ':::'

    def __autoSave(method) -> Callable:
        '''
        decorator to persist the permissions instance to disk
        
        Note:
            This decorator is only visible in the class scope and its NOT a static method
        '''

        def __perms_decorated_func(instance, *args, **kwargs):
            if (response := method(instance, *args, **kwargs)):
                instance.__saveState()
            return response

        return __perms_decorated_func

    def __saveState(self) -> Response:
        '''
        decorator to persist the permissions instance to disk
        
        Note:
            This decorator is only visible in the class scope and its NOT a static method
        '''
        # print('xxx')
        self.__lastModified = dates.currentTimestamp()
        data = encrypt(encodeJSON(self.export()), password=self.__id)
        with Handle(self.__dbFilePath, tables=Permissions.__dbTables, readonly=False, useWALMode=True, returnKISAResponse=True) as handle:
            if not (resp := handle.insert(self.__dbTableName, [
                dates.currentTimestamp(),
                data
            ])):
                print(f'permissions save error: {resp.log}')
                return resp

        return Ok()
    
    def __loadFromDatabase(self) -> Response:
        '''
        load the permissions instance from disk
        '''
        with Handle(self.__dbFilePath, tables=Permissions.__dbTables, readonly=True, returnKISAResponse=True) as handle:
            resp = handle.fetch(Permissions.__dbTableName, ['details'],'1 order by rowid desc',[], limit=1)
            if not resp:
                return resp

            if not resp.data:
                return Error('no-saved-data')

            data = resp.data[0][0]

            try:
                data = decrypt(data, password=self.__id)
            except:
                return Error('failed to decrypt saved permissions')

            try:
                data = decodeJSON(data)
            except:
                return Error('failed to parsed decrypted saved permissions')


            self.__id = data['id']

            self.__users = data['users']
            for role in (roles:=data.get('roles',{})):
                self.__users[self.__formatUserAsRole(role)] = roles[role]

            self.__lastModified = data['lastModified']

            self.__globalPermissions = data['globalPermissions']

            self.__resources = data['resources']
            if self.anyResource not in self.__resources:
                self.__resources[self.anyResource] = {}

            if self.mainResource not in self.__resources:
                self.__resources[self.mainResource] = {}

            return Ok()
        return Error('could not load permissions-db')

    def __formatUserAsRole(self, user:str) -> str:
        '''
        format a user as a role for internal use
        '''
        return f'{self.__roleMarker}{user}'

    def __formatRoleAsUser(self, role:str) -> str:
        '''
        format a role as a user for internal use
        '''
        return role[len(self.__roleMarker):]

    def __userIsARole(self, user:str) -> bool:
        '''check is a user is formated as a role'''
        return user.startswith(self.__roleMarker)

    def __shrinkExpandedPermissions(resource:dict[str,bool]) -> dict[str,bool]:
        '''
        shrink resource permissions to remove redundancies in the description

        Args:
            resource(dict[str,bool]): resource permissions to shrink in format 
            ```
                {
                    "permission1": bool,
                    ...
                }
            ```
        Note:
            the returned resource permissions are in the same format as the input format
        
        Note:
            the function is available in the class but is NOT a static method
        '''
        
        totalCount = len(resource.keys())

        trueCount = list(resource.values()).count(True)
        falseCount = totalCount - trueCount

        # defaultValue = trueCount >= falseCount # if you want *:True if there is a tie between True's and False's
        defaultValue = trueCount > falseCount

        toRemove = list(filter(lambda permission: defaultValue==resource[permission], resource))

        for permission in toRemove: del resource[permission]

        resource['*'] = defaultValue

        return resource

    def __superShrinkExpandedPermissions(shrankPermissions:dict[str, dict[str,bool]]) -> dict[str, dict[str,bool]]:
        '''
        super shrink permissions(that already went through `__shrinkExpandedPermissions`) to remove further redundancies

        Args:
            shrankPermissions(dict[str, dict[str,bool]]): permissions to super-shrink in format 
            ```
                {
                    "resource1":{
                        "permission1": bool,
                        ...
                    },
                    ...
                }
            ```
        Note:
            the returned permissions are in the same format as the input format
        
        Note:
            the function is available in the class but is NOT a static method
        '''

        # exclude `main` from the resources to super shrink...
        main = shrankPermissions['main']
        del shrankPermissions['main']

        values = []
        for resourceName in shrankPermissions:
            resource = shrankPermissions[resourceName]
            values += list(resource.values())
        
        values = list(set(values))

        result = (len(values)==1 and {'*':{'*':values[0]}}) or shrankPermissions
        result.update({'main':main})

        return result

    def __clean(method) -> Callable:
        '''
        decorator to prune unwanted nodes eg after deleting permissions/resources or after syncing resource permissions

        Note:
            This decorator is only visible in the class scope and its NOT a static method        
        '''
        def __perms_decorated_func(instance, *args, **kwargs):
            if (response := method(instance, *args, **kwargs)):
                self:Permissions = instance
                with Permissions.__locks[instance.__id]:
                    for user in (users := self.__users):
                        resources = users[user]
                        for resource in (list(resources.keys())):
                            if resource == self.anyResource:
                                continue
                            if resource not in self.__resources:
                                del resources[resource]
                                continue

                            for permission in list(resources[resource].keys()):
                                if permission == self.anyPermission:
                                    continue
                                if not (permission in self.__resources[resource] or permission in self.__globalPermissions):
                                    del resources[resource][permission]

                        expandedPermissions = self.getUserExpandedPermissions(user).data
                        for resourceName in expandedPermissions:
                            expandedPermissions[resourceName] = Permissions.__shrinkExpandedPermissions(expandedPermissions[resourceName])

                        users[user] = Permissions.__superShrinkExpandedPermissions(expandedPermissions)

            return response

        return __perms_decorated_func

    @__autoSave
    @__clean
    def __setUserPermission(self, user:str, resource:str, permission:str, status:bool) -> Response:
        '''
        attempt to set a user's permission in a resource

        Args:
            user(str): the user who'se permission we need to set
            resource(str): the resource with the permission to be set
            permission(str): the target permission to set
            status(bool): the new permission state
        '''
        if user not in self.__users:
            return Error(f'{Permissions.__getCallStack()} user `{user}` not registered in permissions')

        if resource not in self.__resources:
            return Error('unknown resource given')

        if (permission not in self.__resources[resource]) and (permission not in self.__globalPermissions):
            return Error(f'permission `{permission}` not registered in resource given')

        # if -1 == self.__users.get(user,{}).get(resource,{}).get(permission,-1):
        #     return Error('permission not found for the user under provided resource')
        
        with Permissions.__locks[self.__id]:
            if resource not in self.__users[user]:
                self.__users[user][resource] = {}
            self.__users[user][resource][permission] = status

        return Ok()


    # accessors and settors...
    @__autoSave
    def addGlobalPermissions(self, permissions:list[str]) -> Response:
        '''
        add global permissions

        Args:
            permissions(list[str]): the list of permission to add as global permissions

        Note:
            permissions already present in global permissions will be ignored
        '''
        if not (response := self.__permissionsListValidator(permissions)):
            return response

        if self.anyPermission in permissions:
            return Error(f'cant add permission `{self.anyPermission}` to global permissions')

        with Permissions.__locks[self.__id]:
            for permission in permissions:
                if permission not in self.__globalPermissions:
                    self.__globalPermissions[permission] = None

        return Ok()

    @__autoSave
    @__clean
    def deleteGlobalPermissions(self, permissions:str|list[str]) -> Response:
        '''
        delete global permissions

        Args:
            permissions(list[str]): the list of permission to delete from global permissions
        '''
        if not isinstance(permissions, list):
            permissions = [permissions]

        with Permissions.__locks[self.__id]:
            # verification loop
            for permission in permissions:
                if permission not in self.__globalPermissions:
                    return Error(f'permission `{permission}` is not a global permission')
                
            # action loop
            for permission in permissions:
                del(self.__globalPermissions[permission])

        return Ok()

    def load(self, exportedData:dict) -> Response:
        '''
        attempt to load the instance from disk
        '''
        return Error('functino not active')

    def export(self) -> dict:
        '''
        export permissions as a dict in the format
        ```
        {
            'version': str,
            'id': str,
            'lastModified': str,
            'globalPermissions': list[str],
            'resources': dict[str, list[str]],
            'users': dict[str, dict[str, dict[str, bool]]],
            'roles': dict[str, dict[str, bool]],
        }
        ```
        '''
        data = {
            'version': self.version,
            'id': self.__id,
            'lastModified': self.__lastModified,
            'globalPermissions':deepcopy(self.__globalPermissions),
            'resources': deepcopy(self.__resources),
            'users': {},
            'roles': {},
        }

        for user in self.__users:
            if not self.__userIsARole(user):
                data['users'][user] = deepcopy(self.__users[user])
            else:
                data['roles'][self.__formatRoleAsUser(user)] = deepcopy(self.__users[user])

        return data

    @__autoSave
    def addResources(self, resources:dict[str, list[str]]) -> Response:
        '''
        attempt to add resources to the permissions instance

        Args:
            resources(dict[str, list[str]]): the resources `dict` in format
        ```
        {
            resource1:str : list[str],
            ...
        }
        ```
        '''
        if not (response := validateWithResponse(resources,Value(dict, self.__resourceDictValidator))):
            return response

        with Permissions.__locks[self.__id]:
            for resource in resources:
                if resource in self.__resources:
                    return Error(f'resource `{resource}` already present')

                # self.__resources[resource] = {permission:resources[resource].index(permission) for permission in resources[resource]}
                self.__resources[resource] = {permission:None for permission in resources[resource]}

        return Ok()

    @__autoSave
    @__clean
    def addUsers(self, users:dict[str, dict[str, dict[str, bool]]]) -> Response:
        '''
        attempt to add users to the permissions instance
        Args:
            users(dict[str, dict[str, dict[str, bool]]]): the resources `dict` in format
        ```
        {
            user1:str : {
                resource1:str : {
                    permission1:str : bool,
                    permission2:str : bool,
                    ...
                },
                ...
            },
            ...
        }
        ```
        '''
        if not (response := validateWithResponse(users,Value(dict, self.__usersDictValidator))):
            return response

        with Permissions.__locks[self.__id]:
            for user in users:
                self.__users[user] = deepcopy(users[user])

        return Ok()

    def addRoles(self, roles:dict[str, dict[str, dict[str, bool]]]) -> Response:
        '''
        attempt to add roles to the permissions instance
        Args:
            users(dict[str, dict[str, dict[str, bool]]]): the resources `dict` in format
        ```
        {
            role1:str : {
                resource1:str : {
                    permission1:str : bool,
                    permission2:str : bool,
                    ...
                },
                ...
            },
            ...
        }
        ```
        '''
        for role in list(roles.keys()):
            if role.startswith(self.__roleMarker): continue

            roles[self.__formatUserAsRole(role)] = roles[role]
            del roles[role]
        
        return self.addUsers(roles)

    @__autoSave
    def deleteUser(self, user:str) -> Response:
        '''delete a user from stored permissions'''
        if user not in self.__users:
            return Error('user/role not found in permissions')

        with Permissions.__locks[self.__id]:
            del(self.__users[user])

        return Ok()

    def deleteRole(self, role:str) -> Response:
        '''delete a role from stored permissions'''
        return self.deleteUser(self.__formatUserAsRole(role))

    def __permissionValueInResource(self, userPermissions:dict[str, dict[str,bool]], resource:str, permission:str) -> bool|None:
        '''
        get permission set value for particular user permissions
        Args:
            userPermissions(dict[str, dict[str,bool]]): user permissions to inspect
            resource(str): the resource to check within the user permissions
            permission(str): the permission of interest

        Note:
            If return value is
                * `bool`: permission was resolved
                * `None`: permission was not resolved 
        '''

        specialResources = [self.mainResource, self.anyResource]

        # this should have been captured earlier but in multithreaded programs, we may get here when the resource has been deleted
        if resource not in self.__resources: 
            return False

        if (resource!=self.anyResource) and not (permission in self.__resources[resource] or permission in self.__globalPermissions):
            return False 

        if resource not in userPermissions: 
            return None if resource not in specialResources else False
        

        resourceDict = userPermissions[resource]

        # check if permission is set
        value = resourceDict.get(permission,None)
        if value != None: return value

        # check if permission '*' is set
        value = resourceDict.get(self.anyPermission,None)
        if value != None: return value

        return None if resource not in specialResources else False
        
    def permissionIsActivated(self, *, user:str='', resource:str='', permission:str='') -> Response:
        '''
        attempt to validate a permission while observing the meaning of
            - `*` resource
            - `*` permission
        where
            * the `*` resource is the last to be evaluated
            * within a resource, the `*` permission is the last to be evaluated

        Args:
            user(str): the target user
            resource(str): the resource of interest
            permission(str): the permissions of interest      
        '''
        if user not in self.__users:
            return Error(f'{Permissions.__getCallStack()} user `{user}` not registered in permissions')

        if resource not in self.__resources:
            return Error('resource not registered in the permissions instance')

        if resource in [self.anyResource]:
            return Error(f'cant use `{resource}` as a resource name when validating a permission')

        if permission in [self.anyPermission]:
            return Error(f'cant use permission `{permission}` when validating a permission')

        userResources = self.__users[user]

        responseObjects = {
            True: Ok(),
            False: Error(f'permission `{permission}` not activated for the user')
        }

        if None == (value := self.__permissionValueInResource(userResources, resource, permission)):
            value = self.__permissionValueInResource(userResources, self.anyResource, permission)

        return responseObjects[value]
        
    @__autoSave
    @__clean
    def addUserPermissions(self, user:str, resources:dict[str, dict[str, bool]],/) -> Response:
        '''
        add user permissions

        Args:
            user(str): the target user
            resources(dict[str, dict[str, bool]]): the resource-permissions to add to the user in the format
        ```
        {
            "resource1": {
                "permission1": bool,
                ...
            },
            ...
        }
        ```
        '''
        if user not in self.__users:
            return Error(f'{Permissions.__getCallStack()} user `{user}` not registered in permissions')

        if not (response := self.__usersPermissionsDictValidator(user, resources)):
            return response

        with Permissions.__locks[self.__id]:
            for resource in resources:
                if resource not in self.__users[user]:
                    self.__users[user][resource] = {}

                permissions = resources[resource]
                for permission in permissions:
                    self.__users[user][resource][permission] = permissions[permission]

        return Ok()

    def addRolePermissions(self, role:str, resources:dict[str, dict[str, bool]],/) -> Response:
        '''
        add role permissions

        Args:
            role(str): the target role
            resources(dict[str, dict[str, bool]]): the resource-permissions to add to the user in the format
        ```
        {
            "resource1": {
                "permission1": bool,
                ...
            },
            ...
        }
        ```
        '''
        return self.addUserPermissions(self.__formatUserAsRole(role), resources)

    @__autoSave
    @__clean
    def deleteUserPermission(self, user:str, resource:str, permission:str) -> Response:
        '''
        delete a permission from a user
        Args:
            user(str): the target user
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        if user not in self.__users:
            return Error(f'{Permissions.__getCallStack()} user not registered in permissions')

        if resource not in self.__resources:
            return Error('resource not registered in permissions')

        if resource not in self.__users[user]:
            return Error('user not subscribed to resource')

        if (permission not in self.__resources[resource]) and (permission not in self.__globalPermissions):
            return Error('permission not registered in the resource')

        if permission not in self.__users[user][resource]:
            return Error('permission not registered to the user')

        with Permissions.__locks[self.__id]:
            del(self.__users[user][resource][permission])

        return Ok()

    def deleteRolePermission(self, role:str, resource:str, permission:str) -> Response:
        '''
        delete a permission from a role
        Args:
            role(str): the target role
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        return self.deleteUserPermission(self.__formatUserAsRole(role), resource, permission)

    @__autoSave
    def activateUserPermission(self, user:str, resource:str, permission:str) -> Response:
        '''
        set a permission from `True`
        Args:
            user(str): the target user
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        return self.__setUserPermission(user, resource, permission, True)

    def activateRolePermission(self, role:str, resource:str, permission:str) -> Response:
        '''
        set a permission from `True`
        Args:
            role(str): the target role
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        return self.activateUserPermission(self.__formatUserAsRole(role), resource, permission)

    @__autoSave
    def deactivateUserPermission(self, user:str, resource:str, permission:str) -> Response:
        '''
        set a permission from `False`
        Args:
            user(str): the target user
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        return self.__setUserPermission(user, resource, permission, False)

    def deactivateRolePermission(self, role:str, resource:str, permission:str) -> Response:
        '''
        set a permission from `False`
        Args:
            role(str): the target role
            resource(str): the resource holding the permission
            permission(str): the permission to delete
        '''
        return self.deactivateUserPermission(user=self.__formatUserAsRole(role), resource=resource, permission=permission)

    @__autoSave
    @__clean
    def deleteResource(self, resource:str) -> Response:
        '''
        delete a resource
        Args:
            resource(str): the resource to delete
        '''
        if resource in [self.anyResource, self.mainResource]:
            return Error(f'cant delete `{resource}` as a resource name')

        with Permissions.__locks[self.__id]:
            if resource not in self.__resources:
                return Error('resource not in permissions instance')
            del(self.__resources[resource])

        return Ok()

    @__autoSave
    def addResourcePermissions(self, resource:str, permissions:str | list[str]) -> Response:
        '''
        add resource permissions
        Args:
            resource(str): the resource to modify
            permissions(str | list[str]): a string(1-line CSV) or `list[str]` of the permissions to add
        Note:
            if a permission is already registered, it'll just be essentially skipped
        '''
        if not isinstance(permissions, list):
            permissions = permissions.split(',')

        if not (response := self.__permissionsListValidator(permissions)):
            return response

        with Permissions.__locks[self.__id]:
            if resource not in self.__resources:
                return Error('resource not in permissions instance')
            for permission in permissions:
                self.__resources[resource][permission] = None

        return Ok()

    @__autoSave
    @__clean
    def deleteResourcePermissions(self, resource:str, permissions:list[str]) -> Response:
        '''
        delete resource permissions
        Args:
            resource(str): the resource to modify
            permissions(str | list[str]): a string(1-line CSV) or `list[str]` of the permissions to be deleted
        '''
        if not (response := self.__permissionsListValidator(permissions)):
            return response

        with Permissions.__locks[self.__id]:
            if resource not in self.__resources:
                return Error('resource not in permissions instance')

            for permission in permissions:
                del(self.__resources[resource][permission])

        return Ok()

    def resourceHasPermission(self, resource:str, permission:str) -> Response:
        '''
        check if resource has a permission registered
        Args:
            resource(str): reource to inspect
            permission(str): permission to check
        '''
        if resource not in self.__resources:
            return Error('resource not in permissions instance')

        return Ok() if permission in self.__resources[resource] else Error('resource has no permission')

    def getUserExpandedPermissions(self, user:str) -> Response:
        '''
        get user permissions but fully expanded ie
            * no resource `*`
            * no permission `*`
        Args:
            user(str): the user whose permissions are to be expanded
        '''

        if user not in self.__users:
            return Error('user not found in permissions instance')

        permissions = {}

        for resource in self.__resources:
            if resource == self.anyResource: continue
            permissions[resource] = {}
            for permission in [p for p in self.__globalPermissions] + [p for p in self.__resources[resource]]:
                permissions[resource][permission] = self.permissionIsActivated(user=user, resource=resource, permission=permission).status

        return Ok(permissions)

    @__autoSave
    @__clean
    def syncGlobalPermissions(self, permissions:list[str]) -> Response:
        '''
        add new UNREGISTERED permissions while leaving all registered permissions intact
        Args:
            permissions(list[str]): the permissions list to sync
        '''
        with Permissions.__locks[self.__id]:
            currentPermissions = self.__globalPermissions
            self.__globalPermissions = {}
            if not (response := self.__permissionsListValidator(permissions)):
                self.__globalPermissions = currentPermissions
                return response

            self.__globalPermissions = {perm:None for perm in permissions}

        return Ok()

    @__autoSave
    @__clean
    def syncResourcePermissions(self, resource:str, permissions:list[str]) -> Response:
        '''
        add new UNREGISTERED permissions while leaving all registered permissions intact
        Args:
            resource(str): the target resource
            permissions(list[str]): the permissions list to sync
        '''
        if resource not in self.__resources:
            return Error('unknown resource given')
        
        if resource in [self.anyResource]:
            return Error(f'cant sync `{resource}` resource')
        
        with Permissions.__locks[self.__id]:
            currentPermissions = self.__resources[resource]
            self.__resources[resource] = {}
            if not (response := self.__permissionsListValidator(permissions)):
                self.__resources[resource] = currentPermissions
                return response

            self.__resources[resource] = {perm:None for perm in permissions}

        return Ok()

    @__autoSave
    @__clean
    def syncUserPermissions(self, user:str, permissions:dict[str, dict[str,bool]]) -> Response:
        '''
        add user permissions while leaving all unprovided registered permissions intact
        Args:
            user(str): the target user
            permissions(dict[str, dict[str,bool]]): the permissions list to sync in the format
        ```
        {
            "resource1":{
                "permission1":bool,
                ...
            },
            ...
        }
        ```
        '''
        if user not in self.__users:
            return Error('[syncUserPermissions ERROR] user not registered in permissions')

        if not (response := self.__usersPermissionsDictValidator(user, permissions, validateUser=False)):
            return response

        with Permissions.__locks[self.__id]:
            self.__users[user] = permissions

        return Ok()

    # validators...
    def __projectIdValidator(self, projectId:str) -> Response:
        '''
        validate project Id
        Args:
            projectId(str): the project ID to validate
        '''
        if not ((' ' not in projectId) and len(projectId) and (not projectId.startswith('__'))):
            return Error('invalid id given. expected non-zero-length string with no spaces and not starting with `__`')

        for sequence in ['..','/']:
            if sequence in projectId:
                return Error(f'`{sequence}` not allowed in the id')

        return Ok()

    def __permissionValidator(self, permission:str) -> Response:
        '''
        validate permission name
        Args:
            permission(str): the name to validate
        '''
        if not (isinstance(permission,str) and (' ' not in permission) and len(permission)):
            return Error('invalid permission, expected string with no spaces')

        return Ok()

    def __permissionsListValidator(self, permissions:list[str]) -> Response:
        '''
        validate all permissions in a list
        Args:
            permissions(list[str]): the list of permissions to validate
        '''
        _permissions = list(set(permissions))
        if len(permissions) != len(_permissions):
            return Error('resource contains duplicate permissions')

        if not permissions and not self.__globalPermissions:
            return Error('no permissions provided given and no global permissions registered')

        permissions = _permissions

        for index, permission in enumerate(permissions):
            if not (rep := self.__permissionValidator(permission)):
                return Error(f'permission at index #{index}(`{permission}`), error:{rep.log}')

            if permission in self.__globalPermissions:
                return Error(f'permission at index #{index}(`{permission}`), error:permission already in global permissions')

        return Ok()

    def __resourceDictValidator(self, resources:dict[str, str|list[str]]) -> Response:
        '''
        validate all resource permissions
        Args:
            resources(dict[str, str|list[str]]): the `dict` of permissions to validate. the `dict` is in format
        ```
        {
            "resource1": list[str], # list of permissions
            ...
        }
        ```

        '''
        for resource in resources:

            if not (isinstance(resource,str) and (' ' not in resource) and len(resource)):
                return Error(f'invalid resource name given(`{resource}`), expected string with no spaces')

            if resource in [self.anyResource, self.mainResource]:
                return Error(f'cant use reserved `{resource}` as a resource name')

            permissions = resources[resource]
            if not isinstance(permissions,list):
                return Error(f'invalid permissions given for resource `{resource}`, expected list[str]')

            if not (rep := self.__permissionsListValidator(permissions)):
                return Error(f'resource `{resource}` error:{rep.log}')

        return Ok()

    def __usersPermissionsDictValidator(self, user:str, resources:dict[str, dict[str, bool]], *, validateUser:bool=True) -> Response:
        '''
        validate user permissions

        Args:
            user(str): target user
            validateUser(bool): wheather or not to validate the user name itself
            resources(dict[str, dict[str, bool]]): resource permissions to validate. format is 
        ```
        {
            "resource1": {
                "permission": bool,
                ...
            },
            ...
        }
        ```

        Note:
            `validateUser:bool`
                * triggers a check of if the user exists. returns Error if the user is not registered
                * triggers a check of the permissions. if the user already has the permission (be if set to True or False), an error is returned

        Note:
            the function is ONLY visible in the clas
        '''
        if validateUser and (user not in self.__users):
            return Error(f'user `{user}` not yet registered')

        if not (isinstance(user,str) and (' ' not in user) and len(user)):
            return Error(f'invalid user given(`{user}`), expected string with no spaces')

        if not isinstance(resources,dict):
            return Error(f'invalid resources given for user `{user}`, expected dict[str, dict[str, bool]]')

        for resource in resources:
            if not (isinstance(resource,str) and (' ' not in resource) and len(resource)):
                return Error(f'invalid resource given(`{user}->{resource}`), expected string with no spaces')

            if (resource not in self.__resources) and (resource != self.anyResource):
                return Error(f'resource `{user}->{resource}` not yet registered')

            permissions = resources[resource]
            if not isinstance(permissions,dict):
                return Error(f'invalid permission given(`{user}->{resource}->{permissions}`), expected dict[str,bool]')

            for permission in permissions:
                if not (response:=self.__permissionValidator(permission)):
                    return Error(f'invalid permission given(`{user}->{resource}->{permission}`), error:{response.log}')

                if not isinstance(permissions[permission], bool):
                    return Error(f'invalid permission value given(`{user}->{resource}->{permission}`), expected bool')

                # if resource==self.anyResource and permission == self.anyPermission:
                #     return Error(f'permission `{permission}` not allowed for resource `{resource}`')

                if (permission not in self.__globalPermissions) and (permission not in self.__resources[resource]) and permission not in [self.anyPermission]:
                    if self.anyResource != resource:
                        return Error(f'permission `{user}->{resource}->{permission}` not defined in resource `{resource}` or global permissions')
                    for _resource in self.__resources:
                        if permission in self.__resources[_resource]:
                            return Ok()
                    return Error(f'permission `{user}->{resource}->{permission}` not defined in any resource or global permissions')

                if validateUser and permission in self.__users[user].get(resource,{}):
                    return Error(f'permission `{user}->{resource}->{permission}` already set to the user')

        return Ok()

    def __usersDictValidator(self, users:dict[str, dict[str, dict[str, bool]]]) -> Response:
        '''
        validate entire users dict before changes can be made
        Args:
            users(dict[str, dict[str, dict[str, bool]]]): data to validate format is
        ```
        {
            "user1":{
                "resource1": {
                    "permission": bool,
                    ...
                },
                ...
            },
            ...
        }

        ```
        '''
        for user in users:

            if not (isinstance(user,str) and (' ' not in user) and len(user)>1):
                return Error(f'invalid user given(`{user}`), expected string with no spaces')

            if user in self.__users:
                return Error(f'user `{user}` already registered')

            if not (response := self.__usersPermissionsDictValidator(user, users[user], validateUser=False)):
                return response

        return Ok()

# authentication decorators...

def __decoratedFunctionReturnsKISAResponse(func:Callable) -> Response:
    '''
    check if the decorated function returns a KISA-response
    Args:
        func(Callable): the function to check for conformity
    '''
    funcName = func.__name__
    returnTypeErrorFound = False
    try:
        # prefer typing.get_type_hints to the inbuild `__annotations__` attribute
        # if func.__annotations__['return'] != Response:
        if get_type_hints(func)['return'] != Response:
            returnTypeErrorFound = True
    except:
        returnTypeErrorFound = True

    if returnTypeErrorFound:
        return Error(f'[authenticator:{funcName}]: decorated function MUST return a KISA-Response object only in its signature')

    return Ok()

def __extractSingleAuthenticatorData(func, _projectId:str|None, _user:str, _resource:str, *funcArgs:tuple, **funcKwargs:dict) -> Response:
    '''
    Args:
        _projectId(str|None): the project id
        _user(str): the user id
        _resource(str): the resource name
        *funcArgs(tuple): any anonymous args to be supplied
        **funcKwargs(dict): any anonymous keyword args to be supplied
    '''
    data = {
        'projectId':None,
        'user':None,
        'resource':None,
    }

    signatureParameters = list(inspect.signature(func).parameters)

    for index, parameterName in enumerate(signatureParameters):
        if index >= len(funcArgs): break

        if (_projectId) and parameterName==_projectId:
            data['projectId'] = funcArgs[index]
            continue
        elif parameterName==_user:
            data['user'] = funcArgs[index]
            continue
        elif parameterName==_resource:
            data['resource'] = funcArgs[index]
            continue

    if not (None!=data['user'] and None!=data['resource']) or (None==data['projectId'] and _projectId!=None):
        for kwarg in funcKwargs:
            if (_projectId) and kwarg==_projectId:
                data['projectId'] = funcKwargs[kwarg]
                continue
            elif kwarg==_user:
                data['user'] = funcKwargs[kwarg]
                continue
            elif kwarg==_resource:
                data['resource'] = funcKwargs[kwarg]
                continue

    return Ok(data) if (None!=data['user'] and None!=data['resource']) else Error('[verifyPermissions]: could not find both the specified `user` and `resource` in the decorated function')

def verifyPermissions(perm:Permissions|str,/,*,user:str, resource:str, permissions:str|list[str], checkAll:bool=True):
    '''
    authorize permission

    Args:
        perm(Permissions|str): the Permissions instance to use for authentication
        user(str): the user to authorize using the `perm` instance. The value passed should be the name of an argument or keyword argument that identifies a user in the decorated function
        resource(str): the resource to authorize using the `perm` instance. The value passed should be the name of an argument or keyword argument that identifies a resource in the decorated function
        permissions(str|list[str]): a single permission or list of permissions to authorize
        checkAll(bool): if `True` then ALL permissions must pass the verification test, otherwise verification will be successful if ANY permission passes the test
    Note:
        `return`: `kisa_utils.response.Response`
    '''

    if not isinstance(permissions, list):
        permissions = [permissions]

    def decorator(func):
        funcName = func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            permissionsInstance = perm
            if not isinstance(permissionsInstance, (Permissions,str)):
                return Error(f'[authenticator:{funcName}]: first decorator argument should be an isntance of `Permissions`')
            
            if not permissions:
                return Error(f'[authenticator:{funcName}]: no permissions registered at function decoration')

            if not (response := __decoratedFunctionReturnsKISAResponse(func)):
                return response

            if not (response:=__extractSingleAuthenticatorData(
                func, 
                None if isinstance(permissionsInstance, Permissions) else permissionsInstance, 
                user, 
                resource, 
                *args, 
                **kwargs
            )):
                return response

            runtimeUser, runtimeResource, projectId = response.data['user'], response.data['resource'], response.data['projectId']


            if projectId:
                if not (response := Permissions.getInstance(projectId)):
                    return response
                permissionsInstance = response.data
            elif not isinstance(permissionsInstance, Permissions):
                return Error(f'arg/kwarg named `{permissionsInstance}` not found. needed to find permissions instance')

            checks = [
                permissionsInstance.permissionIsActivated(user=runtimeUser, resource=runtimeResource, permission=permission)
                for permission in permissions
            ]

            if checkAll and not all(checks):
                return [response for response in checks if not response][0]
            else:
                if not any(checks):
                    return checks[0]

            response = func(*args, **kwargs)
            if not isinstance(response, Response):
                return Error(f'[authenticator:{funcName}]: decorated function did not return a KISA-Response object')
            return response

        return wrapper

    return decorator
