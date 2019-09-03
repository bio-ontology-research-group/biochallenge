@Grapes(
    @Grab(group='org.apache.jena', module='jena-arq', version='3.12.0')
)

import org.apache.jena.query.*
import org.apache.jena.rdf.model.RDFNode
import java.text.SimpleDateFormat

class SubChallenge {

    def sparqlquery = null
    def sparqlendpoint = null
    Integer numberOfVersions = 0
    def directory = null

    SubChallenge(dir) {
	this.directory = dir
    }

    SubChallenge(dir, query, endpoint) {
	this.directory = dir
	this.sparqlquery = query
	this.sparqlendpoint = endpoint
    }

    protected Map runSPARQLQuery() {
	Map m = [:]
	Query query = QueryFactory.create( this.sparqlquery )
	QueryExecution qe = QueryExecutionFactory.sparqlService(this.sparqlendpoint, query)
	ResultSet resultSet = qe.execSelect()
	while (resultSet.hasNext()) {
	    def row = resultSet.next()
	    // check here evidence codes
	    m[row['prot']] = row['dis']
	}
	m
    }
    
    public void generateNewVersionFromSPARQL() {
	def date = new Date()
	def sdf = new SimpleDateFormat("dd-MM-yyyy")
	def pd = sdf.format(date)
	new File(this.directory + "/"+pd + "/").mkdirs()
	def map = runSPARQLQuery()
	def fout = new PrintWriter(new BufferedWriter(new FileWriter(this.directory + "/"+pd + "/" + "data.tsv")))
	map.each { p, d ->
	    fout.println("$p\t$d")
	}
	fout.flush()
	fout.close()
    }
}

def query = new File("challenge-disease.sparql").getText()

def challenge = new SubChallenge("./disease/", query, "https://sparql.uniprot.org/sparql/")

challenge.generateNewVersionFromSPARQL()

