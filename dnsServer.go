package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/tatsushid/go-fastping"
)

var dns map[string]string // maps hostname to IP address

var alive map[string]bool                         // maps hostname to status (true = alive)
var pingTicker = time.NewTicker(20 * time.Second) // time between pings
var pinger = fastping.NewPinger()                 // pings the IPs

var portNumber string
var debug bool
var udp bool //use UDP instead of ICMP

/*
request handling functions
Valid Requests:
  /hosts        print the entries in DNS
  /hostsalive   print the active entries in DNS
  /hostsjson    print the entries in DNS as JSON
  /ipaddr~name  update the entry for name with new ipaddr
*/
func hosts(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, prettify(DNS))
}

func hostsalive(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, prettify(getFilteredDNS()))
}

func hostsjson(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	fmt.Fprintf(w, jsonify(DNS))
}

func hostsalivejson(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	fmt.Fprintf(w, jsonify(getFilteredDNS()))
}

func ipname(w http.ResponseWriter, r *http.Request) {
	if strings.Contains(r.URL.Path, "~") {
		pdebug("IP of request: " + r.RemoteAddr)
		args := strings.Split(r.URL.Path[1:], "~")
		splitIP := strings.Split(r.RemoteAddr, ":")
		requestIP := splitIP[:len(splitIP)-1]        //removes what's after the last ':' (done this way bc IP6)
		if args[0] == strings.Join(requestIP, ":") { //if the ip sending the request == the ip part of the requested
			DNS[args[1]] = args[0]
			writeDNS()
			fmt.Fprintf(w, "Updating "+args[1]+" to "+args[0])
		} else {
			fmt.Fprintf(w, "Error: the IP being set doesn't match the IP of the client")
		}

	} else {
		fmt.Fprintf(w, "\n\t\tBad Request\n\n\t(did you mean to go to /hosts?)")
	}
}

///////////////////////
// utility functions //
///////////////////////

//converts a DNS-type map into json
func jsonify(m map[string]string) string {
	bytes, err := json.Marshal(m)
	checkErr(err, "couldn't marshal in jsonify")
	return string(bytes)
}

//converts a DNS-type map into a pretty, readable string
func prettify(m map[string]string) string {
	ret := ""
	for hostname, ipaddr := range m {
		ret += ipaddr + "\t\t" + hostname + "\n"
	}
	return ret
}

//returns a filtered DNS: only robots that are alive
func getFilteredDNS() map[string]string {
	ret := make(map[string]string)
	for hostname, ipaddr := range DNS {
		if alive[hostname] {
			ret[hostname] = ipaddr
		}
	}
	return ret
}

//finds key (hostname) given value (ip)
//assumes alive is one-to-one and onto
func lookup(ip string) string {
	for hostname, ipaddr := range DNS {
		if ip == ipaddr {
			return hostname
		}
	}
	return "NOT FOUND"
}

//error helper, prints error message if there's an error
func checkErr(err error, message string) {
	if err != nil {
		log.Printf("Error: %s\n", message)
		log.Println(err)
	}
}

func pdebug(message string) {
	if debug {
		fmt.Println(message)
	}
}

///////////////////
// alive updater //
///////////////////

// periodically updates
//meant to be run as a goroutine alongside the server
func updateAlive() {
	for {

		//reinstantiates alive to clear the entries
		//otherwise, values would stay in forever
		alive = make(map[string]bool)

		// reinstantiates the pinger to clear the addresses
		// there is a RemoveAddr(), but no function to list addresses
		pinger = fastping.NewPinger()

		if UDP {
			pinger.Network("udp")
		}
		pinger.OnRecv = func(addr *net.IPAddr, rtt time.Duration) {
			pdebug("IP Addr: " + addr.String() + " receive, RTT: " + string(rtt) + "\n")
			alive[lookup(addr.String())] = true
		}
		pinger.OnIdle = func() {
			//fmt.Println("done pinging")
		}

		// add each ip from DNS as candidate ips that will be pinged
		for _, ipaddr := range DNS {
			pinger.AddIP(ipaddr)
		}
		err := pinger.Run()
		checkErr(err, "there was a problem running the pinger")

		<-pingTicker.C // waits on ticker
	}
}

///////////////////
// I/O functions //
///////////////////

// reads a previously saved DNS from disk
func loadDNS() {
	pdebug("reading from .localDNS")
	bytes, err := ioutil.ReadFile(".localDNS")
	checkErr(err, "couldn't read from '.localDNS'")
	err = json.Unmarshal(bytes, &DNS)
	checkErr(err, "couldn't unmarshal data read from '.localDNS'")
}

// saves the DNS to disk by marshalling it then writing it to '.localDNS'
func writeDNS() {
	pdebug("writing to .localDNS")
	bytes, err := json.Marshal(DNS)
	checkErr(err, "couldn't marshal the DNS")
	err = ioutil.WriteFile(".localDNS", bytes, 0644)
	checkErr(err, "couldn't write to '.localDNS'")
}

func main() {
	//handles flags
	flag.BoolVar(&debug, "debug", false, "print debug info")
	flag.BoolVar(&udp, "udp", false, "ping with UDP instead of ICMP")
	flag.StringVar(&portNumber, "port", "7979", "port number")
	flag.Parse()

	//load DNS from .localDNS
	loadDNS()

	//start goroutine to update alive
	go updateAlive()

	//map server functions
	http.HandleFunc("/hosts", hosts)
	http.HandleFunc("/hostsalive", hostsalive)
	http.HandleFunc("/hostsjson", hostsjson)
	http.HandleFunc("/hostsalivejson", hostsalivejson)
	http.HandleFunc("/", ipname) // catches all other paths

	//starts server
	fmt.Println("starting server on port " + portNumber)
	log.Fatal(http.ListenAndServe(":"+portNumber, nil))
}
