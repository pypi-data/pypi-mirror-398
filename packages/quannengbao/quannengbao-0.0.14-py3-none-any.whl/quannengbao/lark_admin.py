import os

import lark_oapi as lark
from lark_oapi.api.auth.v3 import (
    InternalTenantAccessTokenRequestBody,
    InternalTenantAccessTokenRequest,
    InternalTenantAccessTokenResponse, InternalAppAccessTokenRequest, InternalAppAccessTokenRequestBody,
    InternalAppAccessTokenResponse,
    # BaseRequest, BaseResponse

)
from lark_oapi.api.drive.v1 import (
    CreatePermissionMemberRequest, BaseMember, CreatePermissionMemberResponse,
    UpdatePermissionMemberResponse, UpdatePermissionMemberRequest, DeleteFileRequest, DeleteFileResponse,
    TransferOwnerPermissionMemberRequest,
    TransferOwnerPermissionMemberResponse, Owner,
    # TransferOwnerPermissionMemberRequestBuilder,
)
from lark_oapi.api.sheets.v3 import (
    CreateSpreadsheetRequest, Spreadsheet,
    CreateSpreadsheetResponse,
    # QuerySpreadsheetSheetRequest, QuerySpreadsheetSheetResponse,
    # MoveDimension, MoveDimensionSpreadsheetSheetRequest, MoveDimensionSpreadsheetSheetResponse, Dimension,
)


# from lark_oapi.api.authen.v1 import (
#     CreateOidcAccessTokenRequest, CreateOidcAccessTokenRequestBody,
#     CreateOidcAccessTokenResponse
# )


class LarkAdmin:
    def __init__(self):
        self.app_id = os.getenv('LARK_APP_ID')
        self.app_secret = os.getenv('LARK_APP_SECRET')
        self.client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.CRITICAL) \
            .build()
        self.folder_token = None
        self.doc_type = None
        self.doc_token = None
        self.title = None
        self.url = None
        self.member_type = None
        self.member_id = None
        self.perm_type = None

        self.creat_info_opt = None
        self.first_sheet_id = None

    @classmethod
    def perm(cls):
        cls.doc_type_lst = ['doc', 'sheet', 'file', 'wiki', 'bitable', 'docx', 'mindnote', 'minutes']
        cls.doc_member_type_lst = ['email', 'openid', 'openchat', 'opendepartmentid', 'userid']
        cls.permission_type_lst = ['view', 'edit', 'full_access']
        print(f"doc_type_lst: {cls.doc_type_lst}")
        print(f"doc_member_type_lst: {cls.doc_member_type_lst}")
        print(f"permission_type_lst: {cls.permission_type_lst}")
        cls.perm_dct = {
            "doc_type_lst": cls.doc_type_lst,
            "doc_member_type_lst": cls.doc_member_type_lst,
            "permission_type_lst": cls.permission_type_lst
        }
        return cls.perm_dct

    def client_info(self):
        return self

    def tenant_access_token(self):
        tenant_t_request: InternalTenantAccessTokenRequest = InternalTenantAccessTokenRequest.builder() \
            .request_body(InternalTenantAccessTokenRequestBody.builder()
                          .app_id(self.app_id)
                          .app_secret(self.app_secret)
                          .build()) \
            .build()
        tenant_t_response: InternalTenantAccessTokenResponse = self.client.auth.v3.tenant_access_token.internal(
            tenant_t_request)
        return tenant_t_response

    def app_access_token(self):
        app_t_request: InternalAppAccessTokenRequest = InternalAppAccessTokenRequest.builder() \
            .request_body(InternalAppAccessTokenRequestBody.builder()
                          .app_id(self.app_id)
                          .app_secret(self.app_secret)
                          .build()) \
            .build()
        app_t_response: InternalAppAccessTokenResponse = self.client.auth.v3.app_access_token.internal(app_t_request)
        return app_t_response

    # # 处理业务结果
    # lark.logger.info(lark.JSON.marshal(app_t_response.raw.content, indent=4))
    # print(app_t_request)

    def creat_sheet(self, title):
        request: CreateSpreadsheetRequest = CreateSpreadsheetRequest.builder() \
            .request_body(Spreadsheet.builder()
                          .title(title)
                          .build()) \
            .build()

        response: CreateSpreadsheetResponse = self.client.sheets.v3.spreadsheet.create(request)

        title = lark.JSON.marshal(response.data.spreadsheet.title, indent=4).replace('"', '')
        folder_token = lark.JSON.marshal(response.data.spreadsheet.folder_token, indent=4).replace('"', '')
        url = lark.JSON.marshal(response.data.spreadsheet.url, indent=4).replace('"', '')
        spreadsheet_token = lark.JSON.marshal(response.data.spreadsheet.spreadsheet_token, indent=4).replace('"', '')

        self.doc_type = 'sheet'
        self.title = title
        self.folder_token = folder_token
        self.url = url
        self.doc_token = spreadsheet_token

        self.creat_info_opt = {
            "title": title,
            "folder_token": folder_token,
            "url": url,
            "spreadsheet_token": spreadsheet_token,
        }

        print(f"表格创建成功,创建信息: {self.creat_info_opt}")
        return self.creat_info_opt

    def del_doc(self, doc_type, doc_token):
        request: DeleteFileRequest = DeleteFileRequest.builder() \
            .file_token(doc_token) \
            .type(doc_type) \
            .build()
        self.doc_type = doc_type
        self.doc_token = doc_token
        response: DeleteFileResponse = self.client.drive.v1.file.delete(request)
        lark.logger.info(lark.JSON.marshal(response.msg, indent=4))
        return response

    def create_permission(self, doc_token, doc_type, member_type, member_id, perm_type):
        request: CreatePermissionMemberRequest = CreatePermissionMemberRequest.builder() \
            .token(doc_token) \
            .type(doc_type) \
            .request_body(BaseMember.builder()
                          .member_type(member_type)
                          .member_id(member_id)
                          .perm(perm_type)
                          .build()) \
            .build()
        self.doc_type = doc_type
        self.doc_token = doc_token
        self.member_type = member_type
        self.member_id = member_id
        self.perm_type = perm_type

        response: CreatePermissionMemberResponse = self.client.drive.v1.permission_member.create(request)
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        print('premission create!')
        return response

    def update_permission(self, doc_token, doc_type, member_type, member_id, perm_type):
        request: UpdatePermissionMemberRequest = UpdatePermissionMemberRequest.builder() \
            .token(doc_token) \
            .member_id(member_id) \
            .type(doc_type) \
            .request_body(BaseMember.builder()
                          .member_type(member_type)
                          .perm(perm_type)
                          .build()) \
            .build()
        self.doc_type = doc_type
        self.doc_token = doc_token
        self.member_type = member_type
        self.member_id = member_id
        self.perm_type = perm_type

        response: UpdatePermissionMemberResponse = self.client.drive.v1.permission_member.update(request)
        lark.logger.info(lark.JSON.marshal(response.data, indent=4))
        print('premission update!')
        return response

    def do_permission(self, doc_token, doc_type, member_type, member_id, perm_type):
        self.create_permission(doc_token, doc_type, member_type, member_id, perm_type)
        self.update_permission(doc_token, doc_type, member_type, member_id, perm_type)

    def trans_owner(self, doc_token, doc_type, member_type, member_id):
        request: TransferOwnerPermissionMemberRequest = TransferOwnerPermissionMemberRequest.builder() \
            .token(doc_token) \
            .type(doc_type) \
            .request_body(Owner.builder()
                          .member_id(member_id)
                          .member_type(member_type)
                          .build()) \
            .build()
        self.doc_type = doc_type
        self.doc_token = doc_token
        self.member_type = member_type
        self.member_id = member_id

        response: TransferOwnerPermissionMemberResponse = self.client.drive.v1.permission_member.transfer_owner(request)
        lark.logger.info(lark.JSON.marshal(response.msg, indent=4))
        return response
