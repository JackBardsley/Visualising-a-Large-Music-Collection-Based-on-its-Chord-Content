import React from "react";
import * as d3 from 'd3';

export class ChartHierSingleHue extends React.Component {
    constructor(props) {
        super(props)
        this.state = { data: null, request_params: null }
    }

    fetchData(request_params) {
        let r_url = ""
        if (request_params.tag_val.length > 0) {
            r_url = "http://127.0.0.1:5000/circHier?tag_val=" + request_params.tag_val.join() + "&tag_name=" + request_params.tag_name
        }
        else {
            r_url = "http://127.0.0.1:5000/circHier"
        }
        fetch(r_url, { mode: 'cors' })
            .then(r => r.json())
            .then(r => this.setState({ data: r, request_params: request_params }))

    }

    componentDidMount() {
        this.fetchData(this.props.request_params);
    }

    componentDidUpdate() {
        if (this.state.request_params !== this.props.request_params) {
            this.fetchData(this.props.request_params)
        }
        if (this.state.data) {
            this.createChart()
        }

    }

    createChart() {
        const svg = d3.select(this.refs[this.props.id + 'chartsvg'])
        svg.selectAll("*").remove()
        const width = this.props.width
        const height = this.props.height
        let order = this.state.data.order
        let sets = this.state.data.sets
        // Filter based on slider support val
        sets = sets.filter(x => x.values > this.props.support / 100)
        const r = (this.props.height / 2) - 50;

        // Filter out nodes from order that all not in filtered sets
        const filtered_set = new Array(... new Set(sets.flatMap(x => x['labels'])))
        order = order.filter(x => filtered_set.includes(x))

        // Calculate radial coordinate from ordered list of nodes
        const sc_radial = d3.scalePoint().domain(order).range([0, Math.PI * 2 - (Math.PI*2/order.length)])

        // Colour map
        const scColor = d3.scaleSequential().domain([0,d3.max(sets.flatMap(x=>x.values))]).interpolator(d3.interpolateYlOrRd)

        // Convert radial coordinate to cartesian
        const node2point = (d) => {
            return { x: r * Math.sin(sc_radial(d)), y: r * Math.cos(sc_radial(d)) }
        }

        // Centre of the circle
        const centre = { x: width / 2, y: width / 2 }

        // Create objects containing node labels and coordinates from list of edges (sets)
        const node_points = order.map(x => ({ "label": x, "coords": node2point(x) }))

        // Calculate inner heirarchy bundling nodes
        let i_nodes = {}
        // For each root note get angle of sub nodes
        for (let i = 0; i < order.length; i++) {
            if (order[i][1] != "b") {
                if (order[i][0] in i_nodes) {
                    i_nodes[order[i][0]].push(sc_radial(order[i]))
                }
                else {
                    i_nodes[order[i][0]] = [sc_radial(order[i])]
                }
            }
            else {
                if (order.slice(0, 2) in i_nodes) {
                    i_nodes[order[i].slice(0, 2)].push(sc_radial(order[i]))
                }
                else {
                    i_nodes[order[i].slice(0, 2)] = [sc_radial(order[i])]
                }
            }
        }

        // Calculate mean angle for each root note
        let root_nodes = {}
        for (const [key, value] of Object.entries(i_nodes)) {
            const mean_angle = Math.atan2( d3.sum(value.map(Math.sin))/value.length , d3.sum(value.map(Math.cos))/value.length)
            root_nodes[key] = { x: r * Math.sin(mean_angle), y: r * Math.cos(mean_angle) }
        }

        // Append node groups
        const nodes_group = svg.selectAll("g")
            .data(node_points)
            .enter()
            .append("g")
            .attr("transform", (d) => {
                var x = centre.x + d.coords.x
                var y = centre.y - d.coords.y
                return "translate(" + x + "," + y + ")"
            })

        // Append node circles to node groups
        const nodes = nodes_group.append("circle")
            .attr("class", "node")
            .attr("r", 5)

        // Text offset
        const labelOffset = 0.06

        // Append text to labels
        const labels = nodes_group.append("text")
            .text((d) => d.label)
            .attr("fill", "black")
            .attr("dx", (d) => d.coords.x * labelOffset)
            .attr("dy", (d) => -d.coords.y * labelOffset)
            .attr("text-anchor", "middle")
            .attr("font-size", 10)


        const beta = this.props.beta
        const lineGen = d3.line().x(d => d.x + centre.x).y(d => centre.y - d.y).curve(d3.curveBundle.beta(beta))

        let path_factor = 1.4

        const links = svg.selectAll("path")
            .data(sets)
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", (d) => lineGen([node2point(d.labels[0]),
            {
                x: root_nodes[d.labels[0][1] === "b" ? d.labels[0].slice(0, 2) : d.labels[0][0]].x / path_factor,
                y: root_nodes[d.labels[0][1] === "b" ? d.labels[0].slice(0, 2) : d.labels[0][0]].y / path_factor
            },
            {
                x: root_nodes[d.labels[1][1] === "b" ? d.labels[1].slice(0, 2) : d.labels[1][0]].x / path_factor,
                y: root_nodes[d.labels[1][1] === "b" ? d.labels[1].slice(0, 2) : d.labels[1][0]].y / path_factor
            },
            node2point(d.labels[1])]))
            .attr("stroke", d => scColor(d.values))
            .attr("fill", "none")
            .attr("stroke-width", 1)
            .attr("stroke-opacity", d => (d.values / d3.max(sets.map(x => x.values))) ** this.props.focus)

        nodes_group.on("mouseenter", (sel) => {
            d3.selectAll(".link")
                .filter(d => d.labels.includes(sel.label))
                .raise()
                .transition(0.1)
                .attr("stroke", "red")
                .attr("stroke-width", 3)
                .attr("stroke-opacity", d => (d.values / d3.max(sets.map(x => x.values))) ** 1)
        })

        nodes_group.on("mouseleave", (sel) => {
            d3.selectAll(".link")
                .filter(d => d.labels.includes(sel.label))
                .transition(0.1)
                .attr("stroke", d => scColor(d.values))
                .attr("stroke-width", 1)
                .attr("stroke-opacity", d => (d.values / d3.max(sets.map(x => x.values))) ** this.props.focus)
        })
    }


    render() {
        return (
            <svg ref={this.props.id + 'chartsvg'} width={this.props.width} height={this.props.height} style={{ display: "block", margin: "auto" }}>

            </svg>
        )
    }

}