# What to Eat Project

The "What to Eat" project is designed using a microservices architecture. Each service is developed and deployed independently, and can be implemented in any language. Services communicate via REST APIs and are containerized using Docker for easy deployment and scalability.

## Microservices

This project consists of the following microservices:

1. **Recipe** (Python): Provides recipe operations and recipe recommendations based on user preferences and ingredients.
2. **Menu**: Provides menu operations and recommendations.
3. **Eat Together**: Manages group eating sessions and coordination.
4. **Profile**: Manages user profiles.
5. **User Interface**: The frontend for the application.
6. **Authentication**: Manage authentication for secure access.
7. **Menu Auto-Update**: Auto-update for the KAIST Cafeteria menu

## Project Structure

```
what-to-eat
├── services
│   ├── recipe
│   ├── menu
│   ├── menu-auto_update
│   ├── eat-together
│   ├── profile
│   ├── auth
│   ├── user-interface
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Getting Started

1. **Clone the Repository**:

   ```cmd
   git clone https://github.com/faizghifari/what-to-eat.git
   cd what-to-eat
   ```

2. **Install Dependencies**:
   Each service has its own dependencies. Refer to the README in each service directory for setup instructions.

3. **Run the Application**:
   Use Docker Compose to start all services:

   ```cmd
   docker-compose up
   ```

4. **Access the Services**:
   - recipe: `http://recipe-service:8000`
   - menu: `http://menu-service:8000`
   - ets: `http://ets-service:8000`
   - profile: `http://profile-service:8000`
   - ui: `http://ui-service:8000`
   - auth: `http://auth-service:8000`
