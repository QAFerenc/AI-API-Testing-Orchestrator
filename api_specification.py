api_details = [
    {
        "path": "/posts/{id}",
        "method": "GET",
        "summary": "Retrieve a post by ID",
        "parameters": [
            {
                "name": "id",
                "location": "path",
                "required": True,
                "type": "integer",
                "minimum": 1
            }
        ],
        "responses": [
            {
                "status": "200",
                "description": "Post found"
            },
            {
                "status": "404",
                "description": "Post not found"
            }
        ]
    },
    {
        "path": "/users/{id}",
        "method": "GET",
        "summary": "Retrieve a user by ID",
        "parameters": [
            {
                "name": "id",
                "location": "path",
                "required": True,
                "type": "integer",
                "minimum": 1
            }
        ],
        "responses": [
            {
                "status": "200",
                "description": "User found"
            },
            {
                "status": "404",
                "description": "User not found"
            }
        ]
    }
]

REFERENCE_EXPECTATIONS = {
    "/posts/1": 200,
    "/posts/999999": 404,
    "/users/1": 200
}
