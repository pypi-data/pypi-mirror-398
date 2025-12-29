"""
Framework-specific patterns for generic privacy scanning

This module defines patterns for different web frameworks and ORMs,
allowing the scanner to work with any codebase regardless of technology stack.
"""

from typing import Dict, List, Any

# ==========================================
# DATABASE ORM PATTERNS
# ==========================================

ORM_PATTERNS = {
    "sqlalchemy": {
        "description": "SQLAlchemy (Python) - Async & Sync",
        "query_functions": ["select", "query", "insert", "update", "delete"],
        "execution_methods": ["execute", "scalar", "scalars", "fetchone", "fetchall"],
        "result_extraction": ["scalar_one", "scalar", "scalars", "first", "one", "all", "fetchone", "fetchall", "fetchmany"],
        "write_operations": ["add", "add_all", "bulk_save_objects", "merge", "delete"],
        "commit_operations": ["commit", "flush"],
        "model_base_classes": ["Base", "DeclarativeBase", "AbstractDeclarativeBase"],
    },
    
    "django": {
        "description": "Django ORM (Python)",
        "query_functions": ["objects.filter", "objects.get", "objects.all", "objects.create"],
        "execution_methods": ["filter", "get", "all", "first", "last", "exists", "count"],
        "result_extraction": ["values", "values_list", "first", "last", "get"],
        "write_operations": ["save", "create", "update", "delete", "bulk_create", "update_or_create"],
        "model_base_classes": ["Model", "models.Model"],
    },
    
    "peewee": {
        "description": "Peewee ORM (Python)",
        "query_functions": ["select", "insert", "update", "delete"],
        "execution_methods": ["execute", "get", "first"],
        "result_extraction": ["get", "first", "dicts", "tuples", "namedtuples"],
        "write_operations": ["save", "create", "insert", "bulk_create"],
        "model_base_classes": ["Model"],
    },
    
    "sqlmodel": {
        "description": "SQLModel (Python) - FastAPI integration",
        "query_functions": ["select"],
        "execution_methods": ["exec", "execute"],
        "result_extraction": ["one", "first", "all", "scalars"],
        "write_operations": ["add", "add_all"],
        "commit_operations": ["commit", "refresh"],
        "model_base_classes": ["SQLModel"],
    },
    
    "tortoise": {
        "description": "Tortoise ORM (Python) - Async",
        "query_functions": ["filter", "get", "all", "create"],
        "execution_methods": ["filter", "get", "all", "first"],
        "result_extraction": ["values", "values_list", "first"],
        "write_operations": ["save", "create", "update", "delete", "bulk_create"],
        "model_base_classes": ["Model"],
    },
    
    # Java/JVM ORMs
    "hibernate": {
        "description": "Hibernate (Java)",
        "query_functions": ["createQuery", "createNativeQuery", "getCriteriaBuilder"],
        "execution_methods": ["getResultList", "getSingleResult", "executeUpdate"],
        "result_extraction": ["getSingleResult", "getResultList", "uniqueResult"],
        "write_operations": ["save", "persist", "merge", "delete", "saveOrUpdate"],
        "commit_operations": ["flush", "commit"],
    },
    
    "jpa": {
        "description": "JPA (Java Persistence API)",
        "query_functions": ["createQuery", "createNamedQuery", "find"],
        "execution_methods": ["getResultList", "getSingleResult"],
        "result_extraction": ["getSingleResult", "getResultList"],
        "write_operations": ["persist", "merge", "remove"],
        "commit_operations": ["flush"],
    },
    
    # JavaScript/TypeScript ORMs
    "typeorm": {
        "description": "TypeORM (TypeScript/JavaScript)",
        "query_functions": ["find", "findOne", "createQueryBuilder", "query"],
        "execution_methods": ["getMany", "getOne", "getRawMany", "execute"],
        "result_extraction": ["getMany", "getOne", "getRawOne", "getRawMany"],
        "write_operations": ["save", "insert", "update", "delete", "remove"],
        "commit_operations": ["save"],
    },
    
    "prisma": {
        "description": "Prisma (TypeScript/JavaScript)",
        "query_functions": ["findUnique", "findMany", "findFirst", "create", "update"],
        "execution_methods": ["findUnique", "findMany", "findFirst"],
        "result_extraction": ["findUnique", "findMany", "findFirst"],
        "write_operations": ["create", "update", "delete", "upsert", "createMany"],
    },
    
    "sequelize": {
        "description": "Sequelize (TypeScript/JavaScript)",
        "query_functions": ["findAll", "findOne", "findByPk", "create"],
        "execution_methods": ["findAll", "findOne", "findByPk"],
        "result_extraction": ["findAll", "findOne", "findByPk", "get"],
        "write_operations": ["save", "create", "update", "destroy", "bulkCreate"],
    },
    
    # Ruby ORMs
    "activerecord": {
        "description": "ActiveRecord (Ruby on Rails)",
        "query_functions": ["where", "find", "find_by", "all", "first", "last"],
        "execution_methods": ["where", "find", "find_by", "all"],
        "result_extraction": ["first", "last", "take", "pluck"],
        "write_operations": ["save", "create", "update", "destroy", "delete"],
    },
}

# ==========================================
# WEB FRAMEWORK PATTERNS
# ==========================================

WEB_FRAMEWORK_PATTERNS = {
    "fastapi": {
        "description": "FastAPI (Python)",
        "request_decorators": ["get", "post", "put", "patch", "delete", "api_route"],
        "request_params": ["Query", "Path", "Body", "Form", "File", "Depends"],
        "response_types": ["JSONResponse", "Response", "HTMLResponse", "StreamingResponse"],
        "dependency_injection": ["Depends"],
    },
    
    "flask": {
        "description": "Flask (Python)",
        "request_decorators": ["route", "get", "post", "put", "patch", "delete"],
        "request_params": ["request.args", "request.form", "request.json", "request.data"],
        "response_types": ["jsonify", "make_response", "Response"],
    },
    
    "django": {
        "description": "Django (Python)",
        "request_params": ["request.GET", "request.POST", "request.body", "request.data"],
        "response_types": ["JsonResponse", "HttpResponse", "HttpResponseRedirect"],
        "view_types": ["View", "APIView", "ViewSet", "GenericAPIView"],
    },
    
    "spring": {
        "description": "Spring Boot (Java)",
        "request_decorators": ["GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "RequestMapping"],
        "request_params": ["RequestParam", "PathVariable", "RequestBody"],
        "response_types": ["ResponseEntity"],
    },
    
    "express": {
        "description": "Express.js (JavaScript/TypeScript)",
        "request_params": ["req.query", "req.params", "req.body"],
        "response_types": ["res.json", "res.send", "res.status"],
    },
    
    "nestjs": {
        "description": "NestJS (TypeScript)",
        "request_decorators": ["Get", "Post", "Put", "Patch", "Delete"],
        "request_params": ["Query", "Param", "Body"],
        "response_types": ["HttpException", "HttpStatus"],
    },
    
    "rails": {
        "description": "Ruby on Rails",
        "request_params": ["params", "params.require", "params.permit"],
        "response_types": ["render", "redirect_to", "respond_to"],
        "controller_methods": ["before_action", "after_action"],
    },
}

# ==========================================
# PII-SENSITIVE MODEL PATTERNS
# ==========================================

PII_MODEL_KEYWORDS = [
    # User-related
    "user", "account", "profile", "member", "customer", "person", "employee",
    "contact", "participant", "subscriber", "client", "patient", "student",
    
    # Auth/Security
    "auth", "authentication", "credential", "password", "token", "session",
    "apikey", "api_key", "secret", "certificate", "permission", "role",
    
    # Personal data
    "address", "location", "phone", "email", "identity", "document",
    "payment", "billing", "card", "transaction", "order", "invoice",
    
    # Privacy-sensitive
    "scan", "analytics", "tracking", "monitoring", "audit", "log",
    "notification", "message", "comment", "feedback", "review",
    
    # Organization
    "organization", "organisation", "company", "tenant", "workspace",
]

# ==========================================
# RESULT EXTRACTION PATTERNS (Generic)
# ==========================================

GENERIC_RESULT_METHODS = [
    # SQLAlchemy-style
    "scalar_one", "scalar", "scalars", "first", "one", "all",
    
    # DB-API style
    "fetchone", "fetchall", "fetchmany", "fetchval",
    
    # Django-style
    "get", "filter", "values", "values_list",
    
    # Generic collection access
    "first", "last", "take", "limit", "offset",
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_supported_frameworks() -> Dict[str, List[str]]:
    """Get list of all supported frameworks by category"""
    return {
        "orms": list(ORM_PATTERNS.keys()),
        "web_frameworks": list(WEB_FRAMEWORK_PATTERNS.keys()),
    }


def detect_framework(code_patterns: List[str]) -> List[str]:
    """
    Detect which frameworks are used based on code patterns
    
    Args:
        code_patterns: List of function names, method calls, imports found in code
    
    Returns:
        List of detected framework names
    """
    detected = []
    
    # Check ORMs
    for framework, patterns in ORM_PATTERNS.items():
        matches = 0
        for pattern_list in [patterns.get("query_functions", []), 
                            patterns.get("execution_methods", [])]:
            for pattern in pattern_list:
                if any(pattern.lower() in code.lower() for code in code_patterns):
                    matches += 1
        
        if matches >= 2:  # Require at least 2 pattern matches
            detected.append(framework)
    
    # Check web frameworks
    for framework, patterns in WEB_FRAMEWORK_PATTERNS.items():
        for pattern_list in patterns.values():
            if isinstance(pattern_list, list):
                for pattern in pattern_list:
                    if any(pattern in code for code in code_patterns):
                        detected.append(framework)
                        break
    
    return detected


def is_pii_sensitive_model(model_name: str) -> bool:
    """
    Check if a model name suggests it contains PII
    
    Args:
        model_name: Name of the database model/table
    
    Returns:
        True if model likely contains PII
    """
    name_lower = model_name.lower()
    return any(keyword in name_lower for keyword in PII_MODEL_KEYWORDS)


def get_db_result_methods() -> List[str]:
    """Get all known database result extraction methods across frameworks"""
    methods = set()
    for orm_patterns in ORM_PATTERNS.values():
        methods.update(orm_patterns.get("result_extraction", []))
    methods.update(GENERIC_RESULT_METHODS)
    return sorted(list(methods))


def get_db_write_methods() -> List[str]:
    """Get all known database write operation methods across frameworks"""
    methods = set()
    for orm_patterns in ORM_PATTERNS.values():
        methods.update(orm_patterns.get("write_operations", []))
    return sorted(list(methods))


# ==========================================
# EXPORT
# ==========================================

__all__ = [
    "ORM_PATTERNS",
    "WEB_FRAMEWORK_PATTERNS",
    "PII_MODEL_KEYWORDS",
    "GENERIC_RESULT_METHODS",
    "get_supported_frameworks",
    "detect_framework",
    "is_pii_sensitive_model",
    "get_db_result_methods",
    "get_db_write_methods",
]
