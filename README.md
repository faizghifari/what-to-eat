# What to Eat Project

The "What to Eat" project is designed using a microservices architecture. Each service is developed and deployed independently, and can be implemented in any language. Services communicate via REST APIs and are containerized using Docker for easy deployment and scalability.

## Microservices

This project consists of the following microservices:

1. **Recipe Recommendation** (Python): Provides recipe recommendations based on user preferences and ingredients.
2. **Menu Recommendation**: Provides menu recommendations.
3. **Eat Together**: Manages group eating sessions and coordination.
4. **Profile**: Manages user profiles.
5. **User Interface**: The frontend for the application.
6. **Menu Service**: Manages menu items and related operations.
7. **User Service**: Handles user-related functionalities such as registration and authentication.
8. **Order Service**: Manages order processing and tracking.

## Project Structure

```
what-to-eat
├── services
│   ├── recipe-recommendation
│   ├── menu-recommendation
│   ├── eat-together
│   ├── profile
│   ├── user-interface
│   ├── menu-service
│   ├── user-service
│   └── order-service
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
   - Recipe Recommendation: `http://localhost:5001`
   - Menu Recommendation: `http://localhost:5002`
   - Eat Together: `http://localhost:5003`
   - Profile: `http://localhost:5004`
   - User Interface: `http://localhost:3000`
   - Menu Service: `http://localhost:3001`
   - User Service: `http://localhost:3002`
   - Order Service: `http://localhost:3003`
