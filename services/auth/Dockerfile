# --- Build stage ---
FROM rust:latest as builder

WORKDIR /usr/src/auth

COPY . .

RUN cargo build --release

# --- Runtime stage ---
FROM debian:bookworm-slim

# Install needed system libs (if any, e.g., openssl)
RUN apt-get update && apt-get install -y libssl-dev ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the compiled binary from the builder stage
COPY --from=builder /usr/src/auth/target/release/auth /app/auth

# Expose the port your service listens on (changed to 8000)
EXPOSE 8000

CMD ["/app/auth"]
