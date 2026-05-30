function getData(){
    return {
        bpm: Math.floor(60 + Math.random()*40),
        temp: (36 + Math.random()*2).toFixed(1),
        stress: ["LOW","MEDIUM","HIGH"][Math.floor(Math.random()*3)]
    }
}

function updateUI(d){
    document.getElementById("bpm").innerText = d.bpm;
    document.getElementById("temp").innerText = d.temp;
}

function predictStress(){
    let d = getData();
    document.getElementById("stress").innerText = d.stress;
}

let ctx = document.getElementById("chart");
let chart = new Chart(ctx, {
    type: "line",
    data: {
        labels: [],
        datasets: [
            {label:"BPM", data: []},
            {label:"Temp", data: []}
        ]
    }
});

function updateChart(){
    let d = getData();
    updateUI(d);

    chart.data.labels.push(new Date().toLocaleTimeString());
    chart.data.datasets[0].data.push(d.bpm);
    chart.data.datasets[1].data.push(d.temp);

    if(chart.data.labels.length > 10){
        chart.data.labels.shift();
        chart.data.datasets.forEach(ds => ds.data.shift());
    }

    chart.update();
}

setInterval(updateChart, 2000);

// CAMERA
let cameraOn = false;
let stream;

async function toggleCamera(){
    let video = document.getElementById("video");

    if(!cameraOn){
        stream = await navigator.mediaDevices.getUserMedia({video:true});
        video.srcObject = stream;
        video.style.display = "block";
        cameraOn = true;
    } else {
        stream.getTracks().forEach(track => track.stop());
        video.style.display = "none";
        cameraOn = false;
    }
}