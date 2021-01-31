from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from math import pi
import base64
import urllib
from urllib.request import urlopen
from io import BytesIO

from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.models.ranges import Range1d
from bokeh.models.graphs import from_networkx
from bokeh.models.markers import Circle
from bokeh.models.glyphs import MultiLine
from bokeh.transform import linear_cmap
from wordcloud import WordCloud, STOPWORDS

# !pip install pyvis
# !pip install dimcli
# from dimcli.core.extras import NetworkViz
from pyvis.network import Network

class Visualization:

    def plot_daily_sentiment(self, tweets):
        # TODO: Move logic from this class to the Analysis class.
        tweets['date'] = tweets['created_at'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))
        
        df_sum = tweets.groupby(['date', 'sent_label']).size().reset_index(name='count')
        df_sum['date'] = pd.to_datetime(df_sum['date'])

        df_pos = df_sum[df_sum['sent_label'] == 'pos']
        # row = {'date':'2020-12-07 00:00:00', 'sentiment':'pos', 'count':300}
        # df_pos = df_pos.append(row, ignore_index=True)
        df_neu = df_sum[df_sum['sent_label'] == 'neu']
        df_neg = df_sum[df_sum['sent_label'] == 'neg']

        plot = figure(plot_width=1135, plot_height=500, x_axis_type="datetime")
        # plot.title.text = 'Positive/Neutral/Negative Tweet Counts Per Day'

        plot.xaxis.axis_label = 'time'
        plot.yaxis.axis_label = 'tweet count'

        xs = [df_pos['date'], df_neu['date'], df_neg['date']]
        ys = [df_pos['count'], df_neu['count'], df_neg['count']]

        # p.multi_line(xs, ys, color=['green', 'grey', 'red'], alpha=0.5, line_width=2)
        # p.circle(df_pos['date'], df_sum['count'], legend_label='positive', fill_color='green', line_color='green', line_width=2)
        # p.circle(df_pos['date'], df_pos['count'], legend_label="positive", fill_color="green", line_color="green", size=6)
        
        plot.line(df_pos['date'], df_pos['count'], legend_label="positive", line_color="green", line_width=2)
        plot.line(df_neu['date'], df_neu['count'], legend_label="neutral", line_color="grey", line_width=2)
        plot.line(df_neg['date'], df_neg['count'], legend_label="negative", line_color="red", line_width=2)

        plot.circle(df_pos['date'], df_pos['count'], size=20, color="green", alpha=0.5)
        plot.circle(df_neu['date'], df_neu['count'], size=20, color="grey", alpha=0.5)
        plot.circle(df_neg['date'], df_neg['count'], size=20, color="red", alpha=0.5)

        # plot.legend.location = "top_left"

        script, div = components(plot)
        # context = super(Visualization, self).get_context_data()
        # context['script'] = script
        # context['div'] = div

        return script, div

    def network_dynamic(self, df):
        graph = nx.from_pandas_edgelist(df, 'word1', 'word2', 'count')

        # Establish which categories will appear when hovering over each node
        HOVER_TOOLTIPS = [("", "@index")]

        #Create a plot — set dimensions, toolbar, and title
        plot = figure(tooltips = HOVER_TOOLTIPS, tools="pan,wheel_zoom,save,reset", active_scroll='wheel_zoom', x_range=Range1d(-10.1, 10.1), y_range=Range1d(-10.1, 10.1), plot_width=1000, title='')

        # Create a network graph object with spring layout
        network_graph = from_networkx(graph, nx.spring_layout, scale=10, center=(0, 0))

        # Set node size and color
        network_graph.node_renderer.glyph = Circle(size=15, fill_color='skyblue')

        # Set edge opacity and width
        network_graph.edge_renderer.glyph = MultiLine(line_alpha=0.5, line_width=1)

        # # add different colors for each node
        # network_graph.node_renderer.data_source.data['color'] = list(G.nodes)
        # network_graph.node_renderer.glyph = Circle(size=15, fill_color=linear_cmap('color', 'Spectral8', min(G.nodes), max(G.nodes)))

        #Add network graph to the plot
        plot.renderers.append(network_graph)

        script, div = components(plot)
        return script, div

    def network_static(self, df):
        # Create figure
        plt.figure(figsize=(15, 6))
        plt.tight_layout()
        plt.box(False)
        # plt.title(title, fontsize=8)

        # Create graph
        graph = nx.from_pandas_edgelist(df, source='word1', target='word2')        
        
        # Draw graph
        nodes = nx.spring_layout(graph, k=None)
        d = dict(graph.degree)
        node_sizes = [v * 250 for v in d.values()]
        colors = [n for n in range(len(graph.nodes()))]
        cmap = plt.cm.RdYlGn
        nx.draw_networkx(graph, pos=nodes, node_size=node_sizes, cmap=cmap, node_color=colors, edge_color='grey', font_size=10, width=0.5)

        # Save graph as image
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png)
        graphic = graphic.decode('utf-8')

        return graphic

    def network_pyvis(self, df):
        G = nx.from_pandas_edgelist(df, edge_attr=True)

        # print(nx.to_dict_of_dicts(G))

        net = Network(height="500px", width="100%", heading='')

        sources = df['source']
        targets = df['target']
        weights = df['weight']

        edge_data = zip(sources, targets, weights)

        for e in edge_data:
            src = e[0]
            dst = e[1]
            w = e[2]

        net.add_node(src, src, title=src)
        net.add_node(dst, dst, title=dst)
        net.add_edge(src, dst, value=w)

        neighbor_map = net.get_adj_list()

        net.from_nx(G)
        # net.show_buttons(filter_=['physics'])

        net.write_html('tweets/temp.html')
        return net.html

    def frequency(self, df, search_term):
        # title = "Most frequent words occurred in the same tweet with '" + search_term + "'"
        plot = figure(x_range=df['word'], plot_width=1135, plot_height=500, title='')
        plot.vbar(x=df['word'], top=df['count'], width=0.9)

        plot.xgrid.grid_line_color = None
        plot.y_range.start = 0

        plot.xaxis.major_label_orientation = pi/4

        script, div = components(plot)
        return script, div

    def word_cloud(self, df):
        text = ''
        for i, row in df.iterrows():
            text += row['hashtag'] + " "

        plt.figure(figsize=(11, 4))
    
        wordcloud = WordCloud(background_color="white", width=800).generate(text)

        plt.imshow(wordcloud, interpolation='bilinear')
        
        plt.axis("off")
        plt.tight_layout()
        plt.box(False)

        image = BytesIO()
        plt.savefig(image, format='png')
        image.seek(0)  # rewind the data
        string = base64.b64encode(image.read())

        image_64 = 'data:image/png;base64,' + urllib.parse.quote(string)
        return image_64