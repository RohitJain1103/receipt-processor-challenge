## Steps to follow:

- **Build the Docker Image**
  Run the following command in the terminal where the `Dockerfile` is located: `docker build -t receipt-processor .`
- **Run the Container**
  Run the container from the built image: `docker run -p 8000:8000 receipt-processor`
- **Access the Application**
  Open your browser or API client (like Postman) and navigate to: `http://localhost:8000/docs`
