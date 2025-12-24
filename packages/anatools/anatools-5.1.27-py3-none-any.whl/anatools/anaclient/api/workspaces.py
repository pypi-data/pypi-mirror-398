"""
Workspaces API calls.
"""

def getWorkspaces(self, organizationId=None, workspaceId=None, cursor=None, limit=100, filters={}, fields=None):
    if fields is None: fields = self.getTypeFields("Workspace")
    fields = "\n".join(fields)
    if filters is None: filters = {}
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "getWorkspaces",
            "variables": {
                "organizationId": organizationId,
                "workspaceId": workspaceId,
                "limit": limit,
                "cursor": cursor,
                "filters": filters
            },
            "query": f"""query 
                getWorkspaces($organizationId: String, $workspaceId: String, $limit: Int, $cursor: String, $filters: WorkspaceFilter) {{
                    getWorkspaces(organizationId: $organizationId, workspaceId: $workspaceId, limit: $limit, cursor: $cursor, filters: $filters) {{
                        {fields}
                    }}
                }}"""})
    return self.errorhandler(response, "getWorkspaces")


def createWorkspace(self, organizationId, name, description='', channelIds=[], volumeIds=[], code=None, tags=[], objective=''):
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "createWorkspace",
            "variables": {
                "organizationId": organizationId,
                "name": name,
                "description": description,
                "channelIds": channelIds,
                "volumeIds": volumeIds,
                "code": code,
                "tags": tags,
                "objective": objective
            },
            "query": """mutation 
                createWorkspace($organizationId: String!, $name: String!, $description: String, $channelIds: [String]!, $volumeIds: [String]!, $code: String!, $tags: [String], $objective: String) {
                    createWorkspace(organizationId: $organizationId, name: $name, description: $description, channelIds: $channelIds, volumeIds: $volumeIds, code: $code, tags: $tags, objective: $objective)
                }"""})
    return self.errorhandler(response, "createWorkspace")


def deleteWorkspace(self, workspaceId):
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "deleteWorkspace",
            "variables": {
                "workspaceId": workspaceId
            },
            "query": """mutation 
                deleteWorkspace($workspaceId: String!) {
                    deleteWorkspace(workspaceId: $workspaceId)
                }"""})
    return self.errorhandler(response, "deleteWorkspace")


def editWorkspace(self, workspaceId, name=None, description=None, channelIds=None, volumeIds=None, ganIds=None, mapIds=None, tags=[], objective=None):
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "editWorkspace",
            "variables": {
                "workspaceId": workspaceId,
                "name": name,
                "description": description,
                "channelIds": channelIds,
                "volumeIds": volumeIds,
                "ganIds": ganIds,
                "mapIds": mapIds,
                "tags": tags,
                "objective": objective
            },
            "query": """mutation 
                editWorkspace($workspaceId: String!, $name: String, $description: String, $channelIds: [String], $volumeIds: [String], $ganIds: [String], $mapIds: [String], $tags: [String], $objective: String) {
                    editWorkspace(workspaceId: $workspaceId, name: $name, description: $description, channelIds: $channelIds, volumeIds: $volumeIds, ganIds: $ganIds, mapIds: $mapIds, tags: $tags, objective: $objective)
                }"""})
    return self.errorhandler(response, "editWorkspace")


def mountWorkspaces(self, workspaces):
    fields = self.getTypeFields("WorkspaceCredentials")
    fields = "\n".join(fields)
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "mountWorkspaces",
            "variables": {
                "workspaces": workspaces
            },
            "query": f"""mutation 
                mountWorkspaces($workspaces: [String]!) {{
                    mountWorkspaces(workspaces: $workspaces) {{
                        {fields}
                    }}
                }}"""})
    return self.errorhandler(response, "mountWorkspaces")



def createWorkspaceWithTemplate(self, templateId, organizationId=None):
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "createWorkspaceWithTemplate",
            "variables": {
                "templateId": templateId,
                "organizationId": organizationId
            },
            "query": """mutation 
                createWorkspaceWithTemplate($templateId: String!, $organizationId: String) {
                    createWorkspaceWithTemplate(templateId: $templateId, organizationId: $organizationId)
                }"""})
    return self.errorhandler(response, "createWorkspaceWithTemplate")


def getTemplates(self, organizationId=None, fields=None):
    if fields is None: fields = self.getTypeFields("WorkspaceTemplate")
    fields = "\n".join(fields)
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "getTemplates",
            "variables": {
                "organizationId": organizationId
            },
            "query": f"""query 
                getTemplates($organizationId: String) {{
                    getTemplates(organizationId: $organizationId) {{
                        {fields}
                    }}
                }}"""})
    return self.errorhandler(response, "getTemplates")


def createTemplateRequest(self, workspaceId, name=None, description=None, documentation=None, organizationIds=None, instance=None, index=None, demoVideo=None, featured=None, keyFeatures=None, license=None, tags=None, thumbnail=None, version=None):
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "createTemplateRequest",
            "variables": {
                "workspaceId": workspaceId,
                "name": name,
                "description": description,
                "documentation": documentation,
                "organizationIds": organizationIds,
                "instance": instance,
                "index": index,
                "demoVideo": demoVideo,
                "featured": featured,
                "keyFeatures": keyFeatures,
                "license": license,
                "tags": tags,
                "thumbnail": thumbnail,
                "version": version
            },
            "query": """mutation 
                createTemplateRequest($workspaceId: String!, $name: String, $description: String, $documentation: String, $organizationIds: [String], $instance: String, $index: Int, $demoVideo: String, $featured: Boolean, $keyFeatures: [String], $license: String, $tags: [String], $thumbnail: String, $version: Int) {
                    createTemplateRequest(workspaceId: $workspaceId, name: $name, description: $description, documentation: $documentation, organizationIds: $organizationIds, instance: $instance, index: $index, demoVideo: $demoVideo, featured: $featured, keyFeatures: $keyFeatures, license: $license, tags: $thumbnail, version: $version)
                }"""})
    return self.errorhandler(response, "createTemplateRequest")


def getTemplateRequests(self, organizationId, templateId=None, fields=None):
    if fields is None: fields = self.getTypeFields("TemplateRequests")
    fields = "\n".join(fields)
    response = self.session.post(
        url = self.url, 
        headers = self.headers, 
        json = {
            "operationName": "getTemplateRequests",
            "variables": {
                "organizationId": organizationId,
                "templateId": templateId
            },
            "query": f"""query 
                getTemplateRequests($organizationId: String!, $templateId: String) {{
                    getTemplateRequests(organizationId: $organizationId, templateId: $templateId) {{
                        {fields}
                    }}
                }}"""})
    return self.errorhandler(response, "getTemplateRequests")
