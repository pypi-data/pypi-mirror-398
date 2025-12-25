from typing import Any, Dict, List

from tortoise import models

from fast_mu_builder.utils.enums import HeadshipType


class HeadshipMixin(models.Model):
    """
    A mixin to handle headship logic for CRUD operations, including create, update, and delete.
    """
    
    class Meta:
        abstract = True


    # Custom method to filter by user's headship (for list queries)
    @classmethod
    async def with_headship(cls, user):
        
        model_headships = cls.headships()        
        query = cls
        
        filtered = False
        
        for model_headship in model_headships:
            from fast_mu_builder.auth.auth import Auth
            user_headships = Auth.user_headships(model_headship['headship_type'])
            
            for user_headship in user_headships:
                if user_headship:
                    
                    if user_headship.headship_type == HeadshipType.GLOBAL:
                        return query
                
                    filtered = True
                
                    ids = await model_headship['model'].filter(
                        **{f"{model_headship['path']}_id": user_headship.headship_type_id}
                    ).prefetch_related(f"{model_headship['path']}").values_list('id', flat=True)
                    
                    query = query.filter(**{f"{model_headship['column']}__in": ids})

        if not filtered and len(model_headships):
            query = query.filter(**{f"{model_headship['column']}__in": ["__NOTHING__"]})

        return query

        
    """
    Abstract base class that defines the `headships()` method.
    
    This method should return a list of dictionaries where each dictionary defines:
      - `model`: The Tortoise ORM model related to the entity (e.g., `Ward`).
      - `headship_type`: The type of headship (from the `HeadshipType` enum).
      - `column`: The foreign key column that links the resource to a headship 
                  (e.g., 'ward_id' for resources linked to wards).
      - `path`: The ORM path for filtering or accessing data through nested relationships.
               This helps identify how the resource is related to a specific entity 
               (e.g., a `Ward` linked via a region > district > council > division).
    
    Classes that inherit this abstract base class must implement their own version of `headships()`
    to define resource-specific headship relationships.

    This allows CRUD operations (create, read, update, delete) to be governed based on headship rules,
    ensuring that only users with the appropriate headship can perform operations on resources.
    """
    
    @classmethod
    def headships(self) -> List[Dict[str, Any]]:
        """
        Abstract method to be implemented by child classes.

        Returns:
            A list of dictionaries, where each dictionary defines:
              - `model`: The ORM model related to this model which is linked with headship rules.
              - `headship_type`: The type of headship (from `HeadshipType` enum).
              - `column`: The field in this model which is the foreign key to the model.
              - `path`: The ORM path for filtering using relationships describing parents of the model.
        """
        pass