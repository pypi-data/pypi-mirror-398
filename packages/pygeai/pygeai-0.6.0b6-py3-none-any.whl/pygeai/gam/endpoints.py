GET_ACCESS_TOKEN_V2 = "oauth/gam/v2.0/access_token"     # POST -> Sends the user credentials to get a new Token
GET_USER_INFO_V2 = "oauth/gam/v2.0/userinfo"            # GET -> Send the access_token obtained in the previous request and get the user info depending on the scopes you have indicated.
GET_AUTHENTICATION_TYPES_V1 = "v1/gam/authentication-types"     # GET -> Get authentication types
IDP_SIGNIN_V1 = "/oauth/gam/signin"     # NO METHOD -> Just generates URL for authentication in browser
