@Grapes([
  @Grab(group='org.semanticweb.elk', module='elk-owlapi', version='0.4.2'),
  @Grab(group='net.sourceforge.owlapi', module='owlapi-api', version='4.1.0'),
  @Grab(group='net.sourceforge.owlapi', module='owlapi-apibinding', version='4.1.0'),
  @Grab(group='net.sourceforge.owlapi', module='owlapi-impl', version='4.1.0'),
  @Grab(group='net.sourceforge.owlapi', module='owlapi-parsers', version='4.1.0'),
  @GrabConfig(systemClassLoader=true)
  ])

import org.semanticweb.owlapi.model.parameters.*
import org.semanticweb.owlapi.apibinding.OWLManager;
import org.semanticweb.owlapi.reasoner.*
import org.semanticweb.owlapi.model.*;
import org.semanticweb.owlapi.io.*;
import org.semanticweb.owlapi.owllink.*;
import org.semanticweb.owlapi.util.*;
import org.semanticweb.owlapi.search.*;
import org.semanticweb.elk.owlapi.ElkReasonerFactory;
import org.semanticweb.elk.owlapi.ElkReasonerConfiguration
import org.semanticweb.elk.reasoner.config.*
import org.semanticweb.owlapi.manchestersyntax.renderer.*
import org.semanticweb.owlapi.formats.*
import java.util.*

def cli = new CliBuilder()
cli.with {
    usage: 'Self'
    h longOpt:'help', 'this information'
    o longOpt:'ontology', 'OWL File', args:1, required:true
//    n longOpt:'new-challenge', 'create a new challenge', args:0, required:false
}
def opt = cli.parse(args)
if( !opt ) {
  return
}

if( opt.h ) {
    cli.usage()
    return
}


OWLOntologyManager manager = OWLManager.createOWLOntologyManager()
OWLOntology ont = manager.loadOntologyFromOntologyDocument(
  new File(opt.o))
OWLDataFactory dataFactory = manager.getOWLDataFactory()
ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor()
OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor)
ElkReasonerFactory reasonerFactory = new ElkReasonerFactory()
// OWLReasoner reasoner = reasonerFactory.createReasoner(ont, config)
// reasoner.precomputeInferences(InferenceType.CLASS_HIERARCHY)
def renderer = new ManchesterOWLSyntaxOWLObjectRendererImpl()
def shortFormProvider = new SimpleShortFormProvider()

def out = new PrintWriter(
    new BufferedWriter(new FileWriter("axioms.txt")))

def ignoredWords = ["\\r\\n|\\r|\\n", "[()]"]


ont.getTBoxAxioms().each { ax ->
    println("---------------")
    print(ax.getClass())
    println(renderer.render(ax).getClass())
    println("---------------")
    
    out.println(renderer.render(ax));
}

out.flush()
out.close()