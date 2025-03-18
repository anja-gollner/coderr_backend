from rest_framework import permissions



class IsBusinessOwnerOrAdmin(permissions.BasePermission):
    """
    Only business users can create offers.
    Only the owner of the offer or an admin can edit/delete it.
    """

    def has_permission(self, request, view):
        """ Global permission check (applies to list & create). """
        if request.method == 'POST':
            user_profile = getattr(request.user, 'profile', None)
            return (
                request.user.is_authenticated and 
                user_profile and 
                user_profile.type == 'business'
            )
        return True

    def has_object_permission(self, request, view, obj):
        """ Object-level permission check (applies to update/delete). """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return obj.business_user == request.user or request.user.is_staff


class IsCustomerOrAdmin(permissions.BasePermission):
    """
    Only customers can access this resource.
    Admin users (is_staff) also have full access.
    """

    def has_permission(self, request, view):
        """ Global permission check (applies to list & create). """
        user_profile = getattr(request.user, 'profile', None)
        return (
            request.user.is_authenticated and 
            user_profile and 
            (user_profile.type == 'customer' or request.user.is_staff)
        )

    def has_object_permission(self, request, view, obj):
        """ Object-level permission check (applies to update/delete). """
        if request.method in permissions.SAFE_METHODS:
            return True

        # Here we use customer_user instead of obj.user
        return obj.customer_user == request.user or request.user.is_staff

    

class IsReviewerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow only the review creator or an admin to update/delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Here we use reviewer instead of obj.user
        return obj.reviewer == request.user or request.user.is_staff

    
