# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of FastDjango framework

## [0.1.0] - 2024-XX-XX

### Added
- Core framework with FastAPI base
- Django-like ORM wrapper using Tortoise ORM
  - Model base class
  - Fields (CharField, TextField, IntegerField, ForeignKey, etc.)
  - Manager with Django-style queries
  - Async QuerySet with chainable API
- Authentication system
  - User, Group, Permission models
  - Password hashing (bcrypt, PBKDF2)
  - Authentication backends
  - Decorators (login_required, permission_required)
  - JWT token support
- Session support
  - Cookie-based sessions
  - Database sessions
  - Async session middleware
- Admin interface
  - Automatic CRUD for models
  - ModelAdmin configuration
  - List view with search/filter
  - Add/Edit forms
- Middleware
  - Session middleware
  - Auth middleware
  - CSRF protection
  - CORS support
- Routing
  - Extended FastAPI Router
  - WebSocket support
  - ViewSet for REST APIs
- Templates
  - Jinja2 integration
  - Django-like filters (date, truncate, etc.)
  - Static file URL helper
- Forms
  - Django-like Form class
  - ModelForm for model-based forms
  - Pydantic schema generation
- CLI Commands
  - startproject
  - startapp
  - runserver
  - migrate
  - makemigrations
  - createsuperuser
  - shell
  - collectstatic
- Signals (async)
  - pre_save, post_save
  - pre_delete, post_delete
  - User login/logout signals
- Utilities
  - Crypto helpers
  - Text utilities (slugify, truncate)
- Messages framework
- Static files handling
- Example blog application

### Notes
- Requires Python 3.11+
- 100% async
- WebSocket native support
- Automatic OpenAPI documentation
