from ox.django.shortcuts import render_to_json_response

class CheckPermissions(object):

    def user_has_perms(self, request):
        '''
            Check if user has permissions for the URL path and method in the request.
        '''
        path, user, method = (request.path, request.user, request.method,)
        #If it is not an API call, always return True
        if not path.startswith("/1.0/"):
            return True
        #Return True for all GET requests
        if method == 'GET':
            return True
        #If request is POST, PUT or DELETE, check if user is authenticated. More fine-grained permissions checks can be handled here
        if method in ['POST', 'PUT', 'DELETE']:
            if not user.is_authenticated():
                return False
            else:
                return True
        #Ideally, should never reach here. #QUESTION: perhaps we want to return False by default?
        return True   


    def process_request(self, request):
        '''
            Return None to allow django request to pass through middleware.
            Return JSON error with status code 403 if user does not have permissions.
        '''
        if self.user_has_perms(request):
            return None
        else:
            return render_to_json_response({'error': 'Insufficient permissions'}, status=403)
