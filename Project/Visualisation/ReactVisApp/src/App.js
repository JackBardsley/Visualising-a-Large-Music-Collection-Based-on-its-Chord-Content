import React, { useState } from "react";
import { ChartCircular } from "./chartCircular";
import { ChartParallel } from "./chartParallelwNodeFilter";
import { ChartHier } from "./chartHier";
import { Options } from "./options"
import {VisParams} from "./visparams"
import {Legend} from "./legend"
import { Container, Row, Col } from 'react-bootstrap'
import { ChartHierSingleHue } from "./chartHierSingleHue";
import { ChartClust } from "./chartClust";
import { ChartParallelClust } from "./chartParallelClust";

// <Chart width={600} height={600} request_params={{tag_val:"jazz", tag_name:"genres"}}/>

export default () => {

  const [requestParams, setRequestParams] = useState({tag_val:["jazz"], tag_name:"genres"})
  const [chartType, setChartType] = useState("Circular")
  const [focus, setFocus] = useState(1)
  const [support, setSupport] = useState(1)
  const [beta,setBeta] = useState(1)
  const [optType,setOptType] = useState(null)

  const handleFilter = (e) => {
    if (e.target.checked == true) {
      requestParams.tag_val.push(e.target.value)
      setRequestParams({"tag_name":"genres","tag_val":requestParams.tag_val})
    }
    else {
      requestParams.tag_val = requestParams.tag_val.filter(x=> x!=e.target.value)
      setRequestParams({"tag_name":"genres","tag_val":requestParams.tag_val})
    }
  }

  const handleChartType = (e) => {
    setChartType(e)
  }

  const handleOptType = (e) => {
    if (e == "AVSDF") {
      setOptType("avsdf")
    }
    if (e == "Baur Brandes") {
      setOptType("bb")
    }
    if (e == "Root Node Order") {
      setOptType(null)
    }
  }
 
  let chart = ""

  if (chartType === "Circular") {
    chart =  <ChartCircular id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support} optType={optType}/>
  }
  else if (chartType === "Parallel")  {
      chart = <ChartParallel id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support} />
  }
  else if (chartType === "Circular Hierarchical") {
    chart = <ChartHier beta={beta} id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support}/>
  }
  else if (chartType === "Circular Hierarchical - Single Hue") {
    chart = <ChartHierSingleHue beta={beta} id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support}/>
  }
  else if (chartType === "Circular Clustered") {
    chart = <ChartClust beta={beta} id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support} optType={optType}/>
  }
  else if (chartType === "Parallel Clustered") {
    chart = <ChartParallelClust beta={beta} id={1} width={800} height={800} request_params={requestParams} focus={focus} support={support}/>
  }

  let legend = ""
  if (requestParams.tag_val.length > 0 || chartType == "Circular Hierarchical - Single Hue") {
    legend = <Legend chartType={chartType} requestParams={requestParams}/>
  }


  return (<>
    <Container fluid>
      <Row>
        <Col>
          <Options chartType={chartType} requestParams={requestParams} handleFilter={handleFilter} handleChartType={handleChartType}/>
        </Col>
      </Row>
      <Row>
        <Col sm={2}>
        </Col>
        <Col>
          {chart}
        </Col>
        <Col sm={2}>
          {legend}
        </Col>
      </Row>
      <Row>
        <Col>
          <VisParams chartType={chartType} support={support} focus={focus} handleSupport={setSupport} 
                    beta={beta} handleBeta={setBeta} handleFocus={setFocus} handleOptType={handleOptType}/>
        </Col>
      </Row>
    </Container>
  </>)
};
