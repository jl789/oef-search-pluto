from crawler_demo.src.python.lib import CrawlerAgentBehaviour
from behaviour_tree.src.python.lib import BehaveTreeExecution
from svg_output.src.python.lib import SvgStyle
from svg_output.src.python.lib import SvgGraph
from svg_output.src.python.lib import SvgElements
from behaviour_tree.src.python.lib import BehaveTreeExecution
from crawler_demo.src.python.lib.SearchNetwork import SearchNetwork, ConnectionFactory


class CrawlerAgents(object):
    def __init__(self, connection_factory):
        self.tree = CrawlerAgentBehaviour.CrawlerAgentBehaviour()
        self.agents = [
            BehaveTreeExecution.BehaveTreeExecution(self.tree),
        ]
        for agent in self.agents:
            agent.set("connection_factory", connection_factory)

    def tick(self):
        _ = [ x.tick() for x in self.agents ]

    def getSVG(self):
        locations = [ ( agent.get('x'), agent.get('y'), ) for agent in self.agents ]
        crawler_dot_style = SvgStyle.SvgStyle({"fill-opacity": 1, " fill": "black", " stroke-width": 0.1})
        dots =  [
            SvgElements.SvgCircle(
                cx=x,
                cy=y,
                r=3,
                style = crawler_dot_style
            )
            for x,y
            in locations
        ]
        return SvgGraph.SvgGraph(*dots)

