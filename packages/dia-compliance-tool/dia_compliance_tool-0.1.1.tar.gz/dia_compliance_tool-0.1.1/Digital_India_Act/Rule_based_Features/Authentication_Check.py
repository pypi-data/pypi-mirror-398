# This is a rule based checking feature for Authentication messages and this needs API endpoints

class Authentication_checker:
    # this class makes a unauthorized call to the api endpoint and sees if it returns 401 or 403 or not return anything
    name = "Authentication required check for Server API"
    description = "Firstly checks if the api enpoint works or not and then if works then checks if APIs enforce authentication"
    usage = "Send the endpoints as input either as a string or as an object with parameter url"
    def check(self, endpoints):
        results = []
        for endpoint in endpoints:
            endpoint = self.normalize(endpoint)
            result = self.check_endpoint(endpoint)
            results.append(result)
        return results

    def normalize(self,endpoint):
        if isinstance(endpoint, str):
            return type("ApiEndpoint",(),{"url":endpoint})
        return endpoint
    
    def check_endpoint(self,endpoint):
        import requests

        try:
            res = requests.get(endpoint.url, headers={})
            # print(res)
            if res.status_code in [401,403,404]: 
                #401, 403 are typical unauthorized and forbidden flags and 404 is  used to hide the resource and often used to stop unauthorized guy to access the page
                return {"endpoint": endpoint.url, "secure":True, "Api Working":True}
            else:
                return {"endpoint":endpoint.url, "secure":False, "Api Working":True}
        
        except Exception as e:
            return {"endpoint": endpoint.url, "secure":False, "error":str(e), "Api Working":False}
        