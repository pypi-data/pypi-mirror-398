# core/viewsets.py
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from colorstreak import log

class DefaultPagination(PageNumberPagination):
    """
    Clase de paginación por defecto para los ViewSets.
    Puedes personalizarla según tus necesidades.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100



class BaseOptimizedViewSet(viewsets.ModelViewSet):
    """
    Clase base para ViewSets optimizados.
    
    """
    queryset = None
    write_serializer_class = None
    update_serializer_class = None
    simple_serializer_class = None
    full_serializer_class = None
    serializer_class = None
    extensions_auto_optimize = True

    permission_classes = [IsAuthenticated]

    pagination_class = DefaultPagination

    filterset_fields = []
    search_fields = []
    ordering_fields = []
    ordering = []

    def get_queryset(self):
        # aqui heredamos de la libreria estandar
        qs = super().get_queryset()
        model_cls = qs.model
        manager = model_cls._default_manager

        if hasattr(manager, 'simple') and self.action == 'list':
            #log.library("| LIBRERIA | Usando QS simple")
            qs = manager.simple()
        elif hasattr(manager, 'full'):
            #log.library("| LIBRERIA | Usando QS full")
            qs = manager.full()

        try:
            #log.library("| LIBRERIA | Filtrando por created_by")
            qs_created_by= qs.filter(created_by=self.request.user)
            return qs_created_by
        except Exception as e:
            log.error(f"| LIBRERIA | Error al filtrar por created_by: {e}")
            log.info("| LIBRERIA | Filtrado sin created_by")
            return qs



    def get_serializer_class(self):
        
        match self.action:
            case 'create' if self.write_serializer_class is not None:
                return self.write_serializer_class
            case 'update' | 'partial_update' if self.update_serializer_class is not None and self.write_serializer_class is not None:
                return self.update_serializer_class
            case 'list' if self.simple_serializer_class is not None:
                return self.simple_serializer_class
            case 'retrieve' if self.full_serializer_class is not None:
                return self.full_serializer_class
            case _ if self.serializer_class is not None:
                # log.warning(f"| LIBRERIA | No se encontró serializer específico para la acción '{self.action}', usando el por defecto.")
                return self.serializer_class
            case _:
                log.error("| LIBRERIA | No se encontró serializer por defecto")
                raise ValueError("No se encontró serializer por defecto")

    def perform_create(self, serializer):
        try:
            #log.library("| LIBRERIA |Guardando con created_by y updated_by")
            serializer.save(created_by=self.request.user, updated_by=self.request.user)
        except Exception as e:
            log.error(f"| LIBRERIA | Error al guardar: {e}")
            log.info("| LIBRERIA | Guardando sin created_by y updated_by")
            serializer.save()

    def perform_update(self, serializer):
        try:
            #log.library("| LIBRERIA | Guardando con updated_by")
            serializer.save(updated_by=self.request.user)
        except Exception as e:
            log.error(f"| LIBRERIA | Error al actualizar: {e}")
            log.info("| LIBRERIA | Guardando sin updated_by")
            serializer.save()
