FROM rust:latest

WORKDIR /usr/src/auth

COPY . .

RUN cargo br

CMD ["/usr/src/auth/target/release/auth"]
