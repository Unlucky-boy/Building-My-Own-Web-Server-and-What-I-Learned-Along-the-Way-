# Building My Own Web Server (and What I Learned Along the Way)
For a long time, “the web” felt a bit like a black box to me.

I’ve built APIs, used frameworks like Flask, and deployed applications without thinking too much about what actually happens between typing a URL and getting a response on the screen. It all worked, but it didn’t really make sense at a deeper level.

So I decided to fix that by building my own web server from scratch, following Ruslan Spivak’s “[Let’s Build A Web Server](https://ruslanspivak.com/lsbaws-part1/)” series. (You can find all the original code here: https://github.com/rspivak/lsbaws/tree/master)

This is not a guide or a tutorial. It’s a short write-up about what I learned, what surprised me, and how this project changed the way I look at backend development.

# **Why build a web server?**
Honestly? Curiosity.

I wanted to understand what frameworks usually hide:
- how a server actually listens for connections
- how an HTTP request looks before it’s parsed
- how responses are built, byte by byte
- and why things like headers and status codes really matter

Building a web server forces you to face all of that directly. There’s no magic  (Just a **LOOOT** of sockets, strings, and a lot more of small details that need to be exactly right.

# **HTTP feels simple… until you implement it**

One of the first things that surprised me is how simple HTTP is AND at the same time, how unforgiving it can be.

At its core, an HTTP request is just text.
But if your response is missing a line break, a header, or the correct status line, the client simply won’t accept it.

When I started manually parsing requests and crafting responses, things finally clicked:

- why `Content-Length` exists
- why browsers behave differently depending on status codes
- why HTTP is stateless by design

After this, HTTP stopped being “something the framework handles” and became something I could reason about and debug.

### **WSGI finally made sense**

Before this project, WSGI was just an acronym I knew I should understand.

Implementing a minimal WSGI-compatible server changed that completely.

I finally saw the clear separation:

- the server handles networking and HTTP
- the application handles logic
- WSGI is just the agreement between the two

That realization made frameworks like Flask feel much less mysterious. They’re not doing magic — they’re just sitting on top of a very clean and well-defined interface.

### **Concurrency is not optional**

A single-process server works fine… until it doesn’t.

As soon as you have more than one client, things start to break down. Implementing process-based concurrency made it very clear why real-world servers can’t afford to handle one request at a time.

This part of the project helped me better understand:

- why blocking I/O is a problem
- how the operating system affects server performance
- why modern servers rely on workers, async I/O, or event loops

Even a simple approach like forking changes everything.

# **Now the part everyone loves: Technical Walkthrough (Python-Based Implementation)**

This server was implemented using a modern version of Python, relying only on the standard library. The goal was not performance or completeness, but clarity and correctness. 🤓☝️

Enough of the yap and let's get to work.

**High‑Level Architecture**

At a high level, the server follows a classic UNIX design:
- Create a TCP socket and listen for incoming connections
- Accept a client connection
- Fork a new process to handle the request
- Read the raw HTTP request from the socket
- Send back a minimal HTTP response
- Reap child processes to avoid zombies
All I/O is blocking, and each connection is handled in its own process. This keeps the control flow explicit and easy to reason about.

**Core Server Loop**

The heart of the server lives in the serve_forever function:

while True:
    client_conn, client_addr = listen_socket.accept()

    pid = os.fork()

    if pid == 0:  # child process
        listen_socket.close()
        handle_request(client_conn)
        client_conn.close()
        os._exit(0)
    else:  # parent process
        client_conn.close()

This pattern highlights a few important ideas:
- The parent process is responsible only for accepting new connections
- Each child process handles exactly one client
- File descriptors must be closed carefully to avoid leaks

Although simple, this model makes the cost and behavior of concurrency very explicit.

**Handling HTTP Requests**

Request handling is intentionally minimal:

```
def handle_request(conn):
    request = conn.recv(1024)
    print(request.decode(errors="ignore"))

    response = b"""\
HTTP/1.1 200 OK
Content-Type: text/plain

Hello, World!
"""
    conn.sendall(response)
```

The server does not fully parse HTTP headers or bodies. Instead, it reads raw bytes from the socket and sends back a static response. This keeps the focus on connection handling rather than protocol completeness.

**Process Management and Signals**

Because the server forks a new process per request, it must also deal with terminated child processes. This is handled using a SIGCHLD signal handler:
```
def reap_children(signum, frame):
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except OSError:
            break
```
Without this, finished child processes would remain as zombies. Handling SIGCHLD makes process lifecycle management explicit, which is often hidden in higher-level servers.

**Design Decisions & Constraints**

This project intentionally prioritizes clarity over abstraction.

Why blocking sockets?

Blocking I/O keeps the execution flow linear and predictable. At this stage, understanding what happens next is more important than maximizing throughput.

Why process-based concurrency?

Using fork() avoids shared-state complexity and mirrors the architecture of early UNIX web servers. It also makes the limitations of this model — memory usage, process overhead — immediately visible.

Why minimal HTTP support?

Implementing a full HTTP parser would significantly increase complexity without adding much educational value here. The goal was to understand how requests move through the system, not to reimplement the entire protocol.
Why this is not production-ready
This server lacks many features required for real-world use, including:
- Proper error handling
- Timeouts and backpressure
- Security considerations
- Graceful shutdown

These omissions are intentional and help explain why production servers are far more complex.

**Key Takeaway From the Implementation**

Writing each layer manually — sockets, request parsing, WSGI glue, and response formatting. Made the entire request–response lifecycle concrete.
Frameworks stopped feeling like magic and started feeling like **well-designed layers built on top of simple ideas**.

# **What this project really gave me**

More than code, this project gave me mental models.

I now:
- trust abstractions more, because I understand what they hide
- debug backend problems with more confidence
- know how concurrency affects server design
- read framework documentation with better intuition
- think about systems in terms of protocols and responsibilities

The web stopped feeling like a black box and started feeling like something *engineered*, not magical.

# References

This project was inspired by:

- [Let’s Build A Web Server - Part 1](https://ruslanspivak.com/lsbaws-part1/)
- [Let’s Build A Web Server - Part 2](https://ruslanspivak.com/lsbaws-part2/)
- [Let’s Build A Web Server - Part 3](https://ruslanspivak.com/lsbaws-part3/)

All credit for the original material goes to Ruslan Spivak.

# Final thoughts
Building a web server from scratch won’t replace Nginx or Apache (and that’s NOT the point).

The point is understanding why those tools exist and what problems they solve. If you work with backend development and have never done this, I strongly recommend trying it at least once.

The lessons reaallyyyy stick.
