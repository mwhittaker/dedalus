function new_graph(elements) {
  return cytoscape({
    container: document.getElementById('pdg'),
    elements: elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#666',
          'label': 'data(id)'
        }
      },
      {
        selector: 'edge',
        style: {
          'label': function(edge) {
            return edge.data('negative') ? '!' : '';
          },
          'width': 3,
          'line-color': function(edge) {
            return edge.data('negative') ? '#ff6961' : '#ccc';
          },
          'target-arrow-color': function(edge) {
            return edge.data('negative') ? '#ff6961' : '#ccc';
          },
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
        }
      }
    ],
    layout: {
      name: 'breadthfirst',
    }
  });
}

function json_to_elements(json) {
  var nodes = [];
  for (var i = 0; i < json.nodes.length; ++i) {
    var node = json.nodes[i];
    nodes.push({
      group: 'nodes',
      data: { id: node.id[0] },
    });
  }

  var edges = [];
  for (var i = 0; i < json.links.length; ++i) {
    var edge = json.links[i];
    edges.push({
      group: 'edges',
      data: {
        negative: edge.negative,
        source: edge.source[0],
        target: edge.target[0],
      },
    });
  }

  return nodes.concat(edges);
}

function main() {
  var app = new Vue({
    el: '#app',
    data: {
      input: '',
      cy: new_graph([]),
    },
    methods: {
      update_pdg: function() {
        var json = JSON.parse(this.input);
        var elements = json_to_elements(json);
        this.cy.destroy();
        this.cy = new_graph(elements);
        this.cy.destroy();
        this.cy = new_graph(elements);
      },
    },
  });

}

window.onload = main;
