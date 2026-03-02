//Custom JS file for the SAMIS APP
function edit_action(items) {
    let edit_btn = document.getElementById("edit");
    let lock_btn = document.getElementById("lock");
    for (let item in items) {
        let text_box = document.getElementById(item);
        text_box.contentEditable = "true";
        lock_btn.style.display = "block";
        edit_btn.style.display = "none";
    }
}

function save_action(marks) {
    let lock_btn = document.getElementById("lock");
    let save_btn = document.getElementById("save");
    for (let mark in marks) {
        let input = document.getElementById("form_" + mark);
        let text_box = document.getElementById(mark);
        console.log(text_box.innerText);
        input.value = text_box.innerText;
        text_box.contentEditable = "false";
        save_btn.style.display = "block";
        lock_btn.style.display = "none";
    }
}

function save_marks() {
    let lock_btn = document.getElementById("lock");
    let save_btn = document.getElementById("save");
    let text_boxes = document.getElementsByName("marks");
    for( let i = 0; i < text_boxes.length; i++){
        let text_box = text_boxes[i];
        let input = document.getElementById("form_" + text_box.id);
        input.value = text_box.innerText;
        text_box.contentEditable = "false";
        save_btn.style.display = "block";
        lock_btn.style.display = "none";
    }
}

function update_selected(selected, index) {
    let selections = document.getElementsByTagName("select");
    for( let i = 0; i < selections.length; i++){
        let selection = selections[i];
        if (selection != selected && selection.options[index].value == selected.options[index].value) {
            //selection.remove(index);
            selection.options[index].disabled = true;
            /*for(var j = 0; j < selection.options.length; j++) {
                if(selection.options[j].innerText == data) {
                    //selection.options[j].disabled = true;
                    selection.remove(j);
            }*/
        } 
    }
}