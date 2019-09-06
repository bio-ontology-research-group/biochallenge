@Grapes(
    @Grab(group='org.apache.jena', module='jena-arq', version='3.12.0')
)

import org.apache.jena.query.*
import org.apache.jena.rdf.model.RDFNode
import java.text.SimpleDateFormat
import groovy.json.*
import java.util.zip.GZIPOutputStream
import java.io.FileOutputStream


class SubChallenge {

    def sparqlquery = null
    def sparqlendpoint = null
    Integer numberOfVersions = 0
    def directory = null

    SubChallenge(File config) {
	if (config.exists()) {
	    JsonSlurper slurper = new JsonSlurper()
	    def json = slurper.parse(config)
	    this.sparqlquery = json.query
	    this.sparqlendpoint = json.endpoint
	    this.directory = json.dir
	}
    }

    SubChallenge(dir) {
	this.directory = dir
	def f = new File(""+dir+"/config.json")
	if (f.exists()) {
	    JsonSlurper slurper = new JsonSlurper()
	    def json = slurper.parse(new File(""+dir+"/config.json"))
	    this.sparqlquery = json.query
	    this.sparqlendpoint = json.endpoint
	}
    }

    SubChallenge(dir, query, endpoint) {
	this.directory = dir
	this.sparqlquery = query
	this.sparqlendpoint = endpoint
	
	def json = JsonOutput.toJson(['endpoint':this.sparqlendpoint, 'query':this.sparqlquery])
	def fout = new PrintWriter(new BufferedWriter(new FileWriter(dir + "/config.json")))
	fout.println(json)
	fout.flush()
	fout.close()
    }

    protected Map runSPARQLQuery(filename) {
	def fout = new PrintWriter(
	    new GZIPOutputStream(new FileOutputStream(filename), true))
	Query query = QueryFactory.create( this.sparqlquery )
	QueryExecution qe = QueryExecutionFactory.sparqlService(this.sparqlendpoint, query)
	ResultSet resultSet = qe.execSelect()
	Set<String> used = new HashSet<String>()
	while (resultSet.hasNext()) {
	    def row = resultSet.next()
	    // check here evidence codes
	    def prot = row['prot'].toString()
	    def val = row['val'].toString()
	    def key = prot.substring(prot.lastIndexOf('/') + 1) + "_" + val.substring(val.lastIndexOf('/') + 1) 
	    if (!used.contains(key)) {
		fout.println("$prot\t$val")
		used.add(key)
	    }
	}
	fout.flush()
	fout.close()
    }
    
    public Integer generateNewVersionFromSPARQL(String dir) {
	try {
	    runSPARQLQuery(dir + "/data.tsv.gz")
	    return 0
	} catch (Exception E) {
	    E.printStackTrace()
	    return -1
	}
    }

}



def cli = new CliBuilder()
cli.with {
    usage: 'Self'
    h longOpt:'help', 'this information'
    c longOpt:'challenge', 'challenge directory', args:1, required:true
//    n longOpt:'new-challenge', 'create a new challenge', args:0, required:false
    u longOpt:'update', 'update challenge data', args:0, required:false
    j longOpt:'json-config', 'path to config file', args:1, required:true
}
def opt = cli.parse(args)
if( !opt ) {
  return
}

if( opt.h ) {
    cli.usage()
    return
}

def challenge = null

if (opt.j) {
    def f = new File(opt.j)
    challenge = new SubChallenge(f)
}

if (opt.c) {
    if (challenge.generateNewVersionFromSPARQL(opt.c) == 0) {
	return 0
    } else {
	System.exit(1)
    }
}

if (opt.n) {
    def name = System.console().readLine 'What is the name of the challenge: '
    println "Name is " + name
    def dir = new File(name)
    if (dir.exists()) {
	println "Challenge already exists, aborting."
	return -1
    } else {
	dir.mkdirs()
    }
    def endpoint = System.console().readLine 'SPARQL endpoint of the challenge: '
    def reader = System.console().reader()
    println "SPARQL Query to retrieve testing data (terminate with empty line):"
    def query = ""
    while (true) {
	def line = reader.readLine()
	if (line.length() > 0) {
	    query += line
	} else { // empty line
	    def chal = new SubChallenge(name, query, endpoint)
	    println "Successfully created challenge \"$name\""
	    return 0
	}
    }
}

if (opt.n == false && opt.u == false) {
    println "You must either update or create a new challenge."
    return -1
}

//def query = new File("challenge-disease.sparql").getText()
//def challenge = new SubChallenge("./disease/", query, "https://sparql.uniprot.org/sparql/")

//challenge.generateNewVersionFromSPARQL()

