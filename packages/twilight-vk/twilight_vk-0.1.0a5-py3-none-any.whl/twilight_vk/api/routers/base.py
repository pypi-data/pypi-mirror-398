from fastapi import APIRouter

class BaseRouter:

    def __init__(self,
                 **kwargs):
        self.router: APIRouter = None
    
    def get_router(self):
        return self.router