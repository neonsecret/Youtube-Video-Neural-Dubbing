/*https://www.pexels.com/video/*/
var video_order = [0,1,2,3,4];

var video_arr = [["distorted-reflections-of-a-lake-surrounding-on-its-water-surface-3230808","Distorted Reflections Of A Lake Surrounding On Its Water Surface","1.2M","November 16, 2019","Ambient_Nature","Distorted Reflections Of A Lake"],["playful-pomeranian-dogs-behind-wooden-fence-6588292","Playful Pomeranian Dogs behind Wooden Face","61.9K","January 24, 2021","Anna Bondarenko","Playful Pomeranian Dogs"],["the-niagara-falls-in-a-close-up-video-5946371","The Niagara Falls In A Close-up Video","1.14M","November 21, 2020","Sarowar Hussain","The Niagara Falls"],["watching-rain-on-the-road-in-worm-s-eye-view-3343679","Watching Rain On The Road In Worm's Eye View","2.87M","December 06, 2019","Ambient_Nature","Watching Rain"],["wind-chime-hanging-on-a-tree-1578318","Wind Chime Hanging On A Tree","501K","November 08, 2018","Deeana Creates","Wind Chimes Hanging"]];

function onClick(element) {
    document.getElementById("img01").src = element.src;
    document.getElementById("modal01").style.display = "block";
}

function onMouseHover(element) {
    element.play();
}

function onMouseLeave(element) {
    element.pause();
}

function onClickPlayNext (element, idx) {
    var nxt_video = element.parentNode.getElementsByClassName("video-title")[idx].innerText;
    console.log(nxt_video);

    for (let i = 0; i < video_arr.length; i++) {
        /*console.log(video_arr[i][5]);*/
        if (nxt_video == video_arr[i][5]) {
            /*console.log(video_arr[i][5]);*/
            var cur_main_video = video_order[0];
            var new_main_video = i;

            video_order.splice(video_order.indexOf(new_main_video),1);
            video_order.splice(0,1,new_main_video);
            video_order.push(cur_main_video);
            
            document.getElementById("video1").src = "assets/" + video_arr[i][0] + ".mp4";
            document.getElementsByClassName("start")[0].getElementsByTagName("h1")[0].innerText = video_arr[i][1];
            document.getElementsByClassName("start")[0].getElementsByTagName("h3")[0].innerText = video_arr[i][2] + " Views | Uploaded at " + video_arr[i][3];

            document.getElementById("user-bio-pic").src = "assets/" + video_arr[i][0] + ".jpg";
            document.getElementsByClassName("user-name")[0].innerText = video_arr[i][4];
            break;
        }
    }
            /*console.log(video_order);*/
            document.getElementById("video2").src = "assets/" + video_arr[video_order[1]][0] + ".mp4";
            document.getElementById("video3").src = "assets/" + video_arr[video_order[2]][0] + ".mp4";
            document.getElementById("video4").src = "assets/" + video_arr[video_order[3]][0] + ".mp4";
            document.getElementById("video5").src = "assets/" + video_arr[video_order[4]][0] + ".mp4";

            document.getElementsByClassName("video-title")[0].innerText = video_arr[video_order[1]][5];
            document.getElementsByClassName("video-title")[1].innerText = video_arr[video_order[2]][5];
            document.getElementsByClassName("video-title")[2].innerText = video_arr[video_order[3]][5];
            document.getElementsByClassName("video-title")[3].innerText = video_arr[video_order[4]][5];

}