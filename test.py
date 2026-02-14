fetch("http://localhost:8000/register", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        username: "TestUser_" + Math.floor(Math.random() * 1000),
        first_name: "Test",
        last_name: "User",
        email: "test" + Math.floor(Math.random() * 1000) + "@example.com",
        password: "password",
        bio: "I am a generated test user.",
        profile_image_url: "" 
    })
})
.then(response => response.json())
.then(data => {
    if (data.token) {
        console.log("Success! User created.");
        console.log("Token:", data.token);
        alert("Test user created successfully! Refresh the User Profiles page to see them.");
    } else {
        console.log("Server response:", data);
    }
})
.catch(error => console.error("Error:", error));
