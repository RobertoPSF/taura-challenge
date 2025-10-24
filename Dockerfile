FROM golang:1.24-bullseye AS builder

WORKDIR /src

RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
    && nuclei -update-templates \
    && CGO_ENABLED=1 go install github.com/projectdiscovery/katana/cmd/katana@latest

FROM python:3.10-bullseye

WORKDIR /app

COPY --from=builder /go/bin/nuclei /go/bin/katana /usr/local/bin/
RUN chmod +x /usr/local/bin/nuclei \
    && chmod +x /usr/local/bin/katana

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python3", "run.py"]
