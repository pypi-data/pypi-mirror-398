import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import pandas as pd
class InteractivePlot:
  def __init__(self):
    pass
  @staticmethod
  def plotInteractivePlot(x,y,pointData, xlabel,ylabel,title):
    
  ########################Angle vs Average Distance
    
  #####################

    df = pd.DataFrame({
    xlabel: x,
    ylabel: y,
    "Data": pointData
    })


    fig = px.scatter(df, x=xlabel, y=ylabel, color=xlabel, hover_data=['Data'])
    fig.update_layout(title=title,
                  xaxis_title=xlabel,
                  yaxis_title=ylabel)
    fig.show()
    
    file = open(f"{title}.html","w")
    fig.write_html(f"{title}.html")
    file.close()


  def plotInteractivePlotCaption(x,y,pointData,colorArray, xlabel,ylabel,title, makeFile,fileName, metal):
    
  ########################Angle vs Average Distance
    
  #####################

    df = pd.DataFrame({
    xlabel: x,
    ylabel: y,
    "Data": pointData,
    "Legend": colorArray
    })

    caption_text = (
      "Interactive plot showing the distribution of structures as functions of S–N–S angle and average S–N bond length.<br>"
      "Moving the cursor over a specific point reveals the properties of the given structure including the values of the S–N–S angle <br>"
      "and the S–N bond length as well as the CSD refcode for the corresponding entry in the Cambridge Structural Database.<br>"
      f"The clustering of structural hits for {metal} indicates that coordination of {metal} to the N atom of TFSI results in a significant<br>"
      "deviation of the geometric/structural properties of the TFSI core structure."
    )

    fig = px.scatter(df, x=xlabel, y=ylabel,color="Legend", symbol="Legend", hover_data=['Data'])
    fig.update_layout(title=title,
                  xaxis_title=xlabel,
                  yaxis_title=ylabel)
    fig.add_annotation(
    text=caption_text,
    xref="paper", yref="paper",
    x=0, y=-0.3,  # Position below the plot
    showarrow=False,
    font=dict(size=14),
    align="left",  # Align text to the left
    )

# Adjust layout to give extra space for the caption
    fig.update_layout(margin=dict(t=40, b=200))  # Increase bottom margin

    fig.show()
    if(makeFile):
      file = open(f"{fileName}.html","w")
      fig.write_html(f"{fileName}.html")
      file.close()

  def plotInteractivePlot(x,y,pointData,colorArray, xlabel,ylabel,title, makeFile,fileName):
    
  ########################Angle vs Average Distance
    
  #####################

    df = pd.DataFrame({
    xlabel: x,
    ylabel: y,
    "Data": pointData,
    "Legend": colorArray
    })

    

    fig = px.scatter(df, x=xlabel, y=ylabel,color="Legend", symbol="Legend", hover_data=['Data'])
    fig.update_layout(title=title,
                  xaxis_title=xlabel,
                  yaxis_title=ylabel)


    fig.show()
    if(makeFile):
      file = open(f"{fileName}.html","w")
      fig.write_html(f"{fileName}.html")
      file.close()


  def InteractiveHistogram(x,pointData, xlabel,title):
    df = pd.DataFrame({
    xlabel: x,
    'Compound': pointData
    })

    fig=px.histogram(df,x=xlabel,color=xlabel,hover_data=['Compound'])
    fig.update_layout(title=title,
                  xaxis_title=xlabel,
                  yaxis_title="Frequency")
    fig.show()
