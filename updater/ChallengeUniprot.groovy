@Grab(group='org.apache.jena', module='jena-arq', version='3.12.0')
@Grab(group='org.codehaus.gpars', module='gpars', version='1.2.1')

import org.apache.jena.query.*
import org.apache.jena.rdf.model.RDFNode
import java.text.SimpleDateFormat
import groovy.json.*
import groovyx.gpars.*
import java.util.concurrent.*


class SubChallenge {
    def THREADS = 8
    def RETRIES = 3
    def sparqlquery = null
    def sparqlendpoint = null
    Integer numberOfVersions = 0
    def directory = null
    def taxa = new LinkedHashSet()

    SubChallenge(File config, String dir) {
//	new File("uniprot-taxa.txt").eachLine { this.taxa.add(it) }
	if (config.exists()) {
	    JsonSlurper slurper = new JsonSlurper()
	    def json = slurper.parse(config)
	    this.sparqlquery = json.query
	    this.sparqlendpoint = json.endpoint
	    this.directory = dir
	}
    }

    
    
    SubChallenge(dir) {
//	new File("uniprot-taxa.txt").eachLine { this.taxa.add(it) }
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
//	new File("uniprot-taxa.txt").eachLine { this.taxa.add(it) }
	this.directory = dir
	this.sparqlquery = query
	this.sparqlendpoint = endpoint
	
	def json = JsonOutput.toJson(['endpoint':this.sparqlendpoint, 'query':this.sparqlquery])
	def fout = new PrintWriter(new BufferedWriter(new FileWriter(dir+"/config.json")))
	fout.println(json)
	fout.flush()
	fout.close()
    }

    Integer getOrganisms() {
	Query query = QueryFactory.create( """
PREFIX keywords:<http://purl.uniprot.org/keywords/> 
PREFIX uniprotkb:<http://purl.uniprot.org/uniprot/> 
PREFIX taxon:<http://purl.uniprot.org/taxonomy/> 
PREFIX ec:<http://purl.uniprot.org/enzyme/> 
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> 
PREFIX skos:<http://www.w3.org/2004/02/skos/core#> 
PREFIX owl:<http://www.w3.org/2002/07/owl#> 
PREFIX bibo:<http://purl.org/ontology/bibo/> 
PREFIX dc:<http://purl.org/dc/terms/> 
PREFIX xsd:<http://www.w3.org/2001/XMLSchema#> 
PREFIX faldo:<http://biohackathon.org/resource/faldo#> 
PREFIX GO:<http://purl.obolibrary.org/obo/GO_> 
PREFIX allie:<http://allie.dbcls.jp/> 
PREFIX CHEBI:<http://purl.obolibrary.org/obo/CHEBI_> 
PREFIX cco:<http://rdf.ebi.ac.uk/terms/chembl#> 
PREFIX codoa:<http://purl.glycoinfo.org/ontology/codao#> 
PREFIX ensembl:<http://rdf.ebi.ac.uk/resource/ensembl/> 
PREFIX ensemblexon:<http://rdf.ebi.ac.uk/resource/ensembl.exon/> 
PREFIX ensemblprotein:<http://rdf.ebi.ac.uk/resource/ensembl.protein/> 
PREFIX ensemblterms:<http://rdf.ebi.ac.uk/terms/ensembl/> 
PREFIX ensembltranscript:<http://rdf.ebi.ac.uk/resource/ensembl.transcript/> 
PREFIX glycan:<http://purl.jp/bio/12/glyco/glycan#> 
PREFIX glyconnect:<https://purl.org/glyconnect/> 
PREFIX identifiers:<http://identifiers.org/> 
PREFIX mesh:<http://id.nlm.nih.gov/mesh/> 
PREFIX mnet:<https://rdf.metanetx.org/mnet/> 
PREFIX mnx:<https://rdf.metanetx.org/schema/> 
PREFIX orthodb:<http://purl.orthodb.org/> 
PREFIX orthodbGroup:<http://purl.orthodb.org/odbgroup/> 
PREFIX patent:<http://data.epo.org/linked-data/def/patent/> 
PREFIX pubmed:<http://rdf.ncbi.nlm.nih.gov/pubmed/> 
PREFIX rh:<http://rdf.rhea-db.org/> 
PREFIX schema:<http://schema.org/> 
PREFIX sh:<http://www.w3.org/ns/shacl#> 
PREFIX sio:<http://semanticscience.org/resource/> 
PREFIX slm:<https://swisslipids.org/rdf/> 
PREFIX sp:<http://spinrdf.org/sp#> 
PREFIX uberon:<http://purl.obolibrary.org/obo/uo#> 
PREFIX up:<http://purl.uniprot.org/core/> 

SELECT DISTINCT ?organism WHERE {

  	VALUES ?eco {
	       <http://purl.obolibrary.org/obo/ECO_0000269> <http://purl.obolibrary.org/obo/ECO_0000303> <http://purl.obolibrary.org/obo/ECO_0000305> <http://purl.obolibrary.org/obo/ECO_0000315>
	       <http://purl.obolibrary.org/obo/ECO_0000314> <http://purl.obolibrary.org/obo/ECO_0000318> <http://purl.obolibrary.org/obo/ECO_0000250> <http://purl.obolibrary.org/obo/ECO_0000304>
	       <http://purl.obolibrary.org/obo/ECO_0000316> <http://purl.obolibrary.org/obo/ECO_0000270> <http://purl.obolibrary.org/obo/ECO_0000266> <http://purl.obolibrary.org/obo/ECO_0007005>
	       <http://purl.obolibrary.org/obo/ECO_0000353> <http://purl.obolibrary.org/obo/ECO_0007001> <http://purl.obolibrary.org/obo/ECO_0000255> <http://purl.obolibrary.org/obo/ECO_0000247>
	} .
	?prot up:reviewed true .
    	[] rdf:subject ?prot ;
                   rdf:predicate up:classifiedWith ;
                   rdf:object ?o ;
                   up:attribution /up:evidence ?eco .
        ?prot up:classifiedWith ?go .
  		?go a owl:Class .
		?prot up:organism ?organism .
}
"""
	)
	QueryExecution qe = QueryExecutionFactory.sparqlService(this.sparqlendpoint, query)
	ResultSet resultSet = qe.execSelect()
	while (resultSet.hasNext()) {
	    def row = resultSet.next()
	    taxa.add(row["organism"])
	}
	return taxa.size()
    }
    
    protected Map runSPARQLQuery() {
	def fout = new PrintWriter(new BufferedWriter(new FileWriter(this.directory+"/data.tsv")))
	GParsPool.withPool(this.THREADS) { pool ->
	    taxa.eachParallel { taxon ->
		println "Doing $taxon..."
		def tries = this.RETRIES
		while (tries > 0 ) {
		    try {
			Query query = QueryFactory.create( this.sparqlquery.replaceAll("TAXON", "<"+taxon+">") )
			QueryExecution qe = QueryExecutionFactory.sparqlService(this.sparqlendpoint, query)
			ResultSet resultSet = qe.execSelect()
			while (resultSet.hasNext()) {
			    def row = resultSet.next()
			    // check here evidence codes
			    //m[row['prot']] = row['val']
			    //println row['prot'].toString()+"\t"+row['val'].toString()
			    fout.println(""+row['prot']+"\t"+row['val'])
			}
			fout.flush()
			tries = -1
		    } catch (Exception E) {
			E.printStackTrace()
		    }
		}
	    }
	}
	fout.flush()
	fout.close()
	null
    }
    
    public Integer generateNewVersionFromSPARQL() {
	try {
//	    new File(this.directory + "/"+pd + "/").mkdirs()
	    def map = runSPARQLQuery()
	    return 0
	} catch (Exception E) {
	    E.printStackTrace()
	    return -1
	}
    }

    public Integer generateNewVersionFromSPARQL(String dir) {
	try {
	    def date = new Date()
	    def sdf = new SimpleDateFormat("dd-MM-yyyy")
	    def pd = sdf.format(date)
//	    new File(this.directory + "/"+pd + "/").mkdirs()
	    def map = runSPARQLQuery()
	    def fout = new PrintWriter(new BufferedWriter(new FileWriter(dir+"/data.tsv")))
	    map.each { p, d ->
		fout.println("$p\t$d")
	    }
	    fout.flush()
	    fout.close()
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
    challenge = new SubChallenge(f, opt.c)
    println "Parallelizing across " + challenge.getOrganisms() + " taxa."
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

