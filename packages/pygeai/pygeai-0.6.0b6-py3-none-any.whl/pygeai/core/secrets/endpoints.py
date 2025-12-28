LIST_SECRETS_V1 = "/v1/secrets"     # GET -> Get secrets (Params: ?name=&id=&start=&count=)
GET_SECRET_V1 = "/v1/secrets/{secretID}"    # GET -> Get secret by Id
CREATE_SECRET_V1 = "/v1/secrets"    # POST -> Create secret
UPDATE_SECRET_V1 = "/v1/secrets/{secretID}"    # PUT -> Update secret by Id
SET_SECRET_ACCESSES_V1 = "/v1/secrets/{secretID}/accesses"    # POST -> Set accesses
GET_SECRET_ACCESSES_V1 = "/v1/secrets/{secretID}/accesses"    # GET -> Get accesses

