/* The code originates from https://www.w3schools.com/howto/howto_js_draggable.asp */
function make_draggable(request) {
    let element_id = request["element_id"];
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    let element = document.getElementById(element_id);
    let handle = document.getElementById(element_id+"_handle");
    if (!element) {
        return
    }

    const isInHandleRegion = (e) => {
        if (!handle) return true;
        const handleRect = handle.getBoundingClientRect();
        if (handleRect && handleRect.height) {
            // Allow dragging anywhere across the card as long as the pointer is within the handle's vertical band.
            return e.clientY >= handleRect.top && e.clientY <= handleRect.bottom;
        }
        // Fallback if getBoundingClientRect isn't available for some reason.
        const elementRect = element.getBoundingClientRect();
        const handleHeight = handle.offsetHeight || 24;
        const offsetY = e.clientY - elementRect.top;
        return offsetY >= 0 && offsetY <= handleHeight;
    };

    // Bind dragging to the whole card but only activate it when the pointer is in the title-bar region.
    element.onmousedown = function(e) {
        e = e || window.event;
        if (!isInHandleRegion(e)) {
            return;
        }
        dragMouseDown(e);
    };
    
    const savedPosition = cardState.getPosition(element_id);
    const position = savedPosition || {"top": "200px", "left": "50px"};
    element.style.top =  position["top"];
    element.style.left =  position["left"];
    cardState.setPosition(element_id, position);
    cardState.ensureVisibilityTracked(element);
    element.style.visibility = 'visible';

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }
    
    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        let top = (element.offsetTop - pos2);
        let left = (element.offsetLeft - pos1);
        if(top < 40) {
            top = 40;
        }
        if(left < -300) {
            left = -300;
        }
        element.style.top =  top + "px";
        element.style.left =  left + "px";
    }
    
    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
        cardState.setPosition(element_id, {"top": element.style.top, "left": element.style.left});
    }
}

register_function("make_draggable", make_draggable);
