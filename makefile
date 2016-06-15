all: dnsServer.go
	go build dnsServer.go

linux32:
	env GOOS=linux GOARCH=386 go build -o dnsServer32 -v dnsServer.go

linux64:
	env GOOS=linux GOARCH=amd64 go build -o dnsServer64 -v dnsServer.go

clean:
	$(RM) dnsServer dnsServer32 dnsServer64
