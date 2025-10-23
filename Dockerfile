FROM golang:1.24-bullseye AS builder

WORKDIR /src

RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

FROM python:3.10-bullseye

WORKDIR /app

COPY --from=builder /go/bin/nuclei /usr/local/bin/nuclei
RUN chmod +x /usr/local/bin/nuclei

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "run.py"]
