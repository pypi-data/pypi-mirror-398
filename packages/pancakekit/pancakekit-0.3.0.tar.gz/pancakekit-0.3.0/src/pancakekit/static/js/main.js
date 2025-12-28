const root_id = '{{ SELF.uid }}';
const WS_URL = '{{ SELF.url }}'.replace(/^http/, 'ws') + '/ws';
let revisions = {};
let registered_functions = {};
let post_rendering_functions = [];
let current_cake = '-';
let selected_toppings = [];
let socket = null;
let reconnect_timeout_ms = 1000;

let pk_request_counter = 0;
const pk_pending_requests = new Map();
const pk_pressable_states = new Map();

const cardState = (() => {
    const positions = {};
    const visibility = {};

    const applyVisibility = (element_id, defaultVisible) => {
        const savedVisibility = visibility[element_id];
        if (typeof savedVisibility === 'boolean') {
            return savedVisibility;
        }
        return defaultVisible;
    };

    return {
        setPosition(element_id, position) {
            positions[element_id] = position;
        },
        getPosition(element_id) {
            return positions[element_id];
        },
        setVisibility(element_id, isVisible) {
            visibility[element_id] = Boolean(isVisible);
        },
        getVisibility(element_id) {
            return visibility[element_id];
        },
        applyToElement(element) {
            if (!element) return;
            const position = positions[element.id];
            if (position) {
                element.style.top = position.top;
                element.style.left = position.left;
            }
            const shouldShow = applyVisibility(element.id, element.style.display !== 'none');
            // Restore stylesheet-defined display when visible (avoids forcing `display: initial` which breaks flex layouts).
            element.style.display = shouldShow ? '' : 'none';
        },
        ensureVisibilityTracked(element) {
            if (!element) return;
            if (typeof visibility[element.id] === 'undefined') {
                visibility[element.id] = element.style.display !== 'none';
            }
        }
    };
})();

function register_function(fname, f) {
    registered_functions[fname] = f;
}

function register_post_rendering_function(f) {
    post_rendering_functions.push(f);
}

function defocus() {
    document.activeElement.blur();
}

function init_socket() {
    socket = new WebSocket(WS_URL);

    socket.onopen = function() {
        reconnect_timeout_ms = 1000;
        go_to_cake('');
    };

    socket.onclose = function() {
        setTimeout(init_socket, reconnect_timeout_ms);
        reconnect_timeout_ms = Math.min(reconnect_timeout_ms * 2, 10000);
    };

    socket.onerror = function(err) {
        console.log(err);
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'updates') {
            if (data.status === 'ok' || data.updates) {
                process_commands(data.commands || []);
                if (data.updates) {
                    check_revisions(data.updates);
                }
            }
            if (data.request_id) {
                pk_resolve_request(data.request_id);
            }
            wait_indicator(false);
        } else if (data.type === 'go_to_response') {
            if (data.status === 'ok') {
                apply_go_to_response(data);
            }
        } else if (data.type === 'revision_payload') {
            apply_revision_payload(data.payload);
        } else if (data.type === 'error') {
            console.log("WS error:", data.msg);
            wait_indicator(false);
        }
    };
}

function send_ws(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    } else {
        console.log("WebSocket not ready");
    }
}

function send_event(topping_id, event_name, params = {}, request_id = null) {
    wait_indicator(true);
    const payload = {
        type: 'event',
        topping_id: topping_id,
        event_name: event_name,
        params: params,
        cake: current_cake
    };
    if (request_id !== null && typeof request_id !== 'undefined') {
        payload.request_id = request_id;
    }
    send_ws(payload);
}

function pk_new_request_id() {
    pk_request_counter += 1;
    return `pk-${Date.now()}-${pk_request_counter}`;
}

function pk_wait_for_request(request_id) {
    return new Promise((resolve) => {
        pk_pending_requests.set(request_id, resolve);
    });
}

function pk_resolve_request(request_id) {
    const resolve = pk_pending_requests.get(request_id);
    if (resolve) {
        pk_pending_requests.delete(request_id);
        resolve();
    }
}

function pk_sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function pk_onclick(element, topping_id, event_name, params = {}) {
    const key = element && element.id ? element.id : topping_id;
    const state = pk_pressable_states.get(key);
    if (state && state.suppressClick) {
        state.suppressClick = false;
        if (state.cleanupTimer) {
            clearTimeout(state.cleanupTimer);
            state.cleanupTimer = null;
        }
        if (!state.active) {
            pk_pressable_states.delete(key);
        }
        return false;
    }
    defocus();
    setTimeout(send_event.bind(element, topping_id, event_name, params), 50);
    return false;
}

function pk_pressable_down(e, element, topping_id, initial_event_name = 'onclick', clickParams = {}) {
    if (!element) return;
    if (e && typeof e.button === 'number' && e.button !== 0) return;

    const key = element.id ? element.id : topping_id;
    let state = pk_pressable_states.get(key);
    if (state && state.active) return;

    state = {
        active: true,
        suppressClick: true,
        element: element,
        topping_id: topping_id,
        initialEvent: initial_event_name,
        params: clickParams || {},
        inflightAck: null,
        inflightPending: false,
        cleanupTimer: null,
        startTimer: null,
        pointerId: e ? e.pointerId : null
    };
    pk_pressable_states.set(key, state);

    if (state.cleanupTimer) {
        clearTimeout(state.cleanupTimer);
        state.cleanupTimer = null;
    }
    try {
        if (e && typeof element.setPointerCapture === 'function') {
            element.setPointerCapture(e.pointerId);
        }
    } catch (_err) {}

    // Fire the initial callback immediately, then start repeat after a delay.
    defocus();
    setTimeout(() => {
        if (!state.active) return;
        const eventName = state.initialEvent || 'onclick';
        if (eventName === 'pressed') {
            const request_id = pk_new_request_id();
            const ack = pk_wait_for_request(request_id);
            state.inflightAck = ack;
            state.inflightPending = true;
            ack.then(() => {
                state.inflightPending = false;
            });
            send_event(topping_id, eventName, state.params, request_id);
        } else {
            send_event(topping_id, eventName, state.params);
        }
    }, 50);

    if (state.startTimer) {
        clearTimeout(state.startTimer);
    }
    state.startTimer = setTimeout(() => pk_pressable_start_repeat(key), 500);
}

function pk_pressable_up(e, element, topping_id) {
    if (!element) return;
    const key = element.id ? element.id : topping_id;
    const state = pk_pressable_states.get(key);
    if (!state) return;

    state.active = false;
    if (state.startTimer) {
        clearTimeout(state.startTimer);
        state.startTimer = null;
    }
    try {
        if (e && typeof element.releasePointerCapture === 'function' && state.pointerId !== null) {
            element.releasePointerCapture(state.pointerId);
        }
    } catch (_err) {}

    // Allow the upcoming click event to be suppressed, then garbage-collect.
    if (state.cleanupTimer) {
        clearTimeout(state.cleanupTimer);
    }
    state.cleanupTimer = setTimeout(() => {
        pk_pressable_states.delete(key);
    }, 1000);
}

async function pk_pressable_start_repeat(key) {
    const state = pk_pressable_states.get(key);
    if (!state || !state.active) return;

    if (state.initialEvent === 'pressed' && state.inflightPending && state.inflightAck) {
        await state.inflightAck;
        if (!state.active) return;
        await pk_sleep(100);
    }

    while (state.active) {
        const request_id = pk_new_request_id();
        const ack = pk_wait_for_request(request_id);
        send_event(state.topping_id, 'pressed', state.params || {}, request_id);
        await ack;
        if (!state.active) break;
        await pk_sleep(100);
    }
}

function coerceBoolean(value) {
    if (typeof value === 'boolean') return value;
    if (typeof value === 'number') return value !== 0;
    if (typeof value === 'string') {
        const v = value.trim().toLowerCase();
        if (['1', 'true', 't', 'yes', 'y', 'on'].includes(v)) return true;
        if (['0', 'false', 'f', 'no', 'n', 'off', ''].includes(v)) return false;
    }
    return Boolean(value);
}

function value_changed(element_id) {
    const element = document.getElementById(element_id);
    if (!element) {
        return;
    }
    wait_indicator(true);
    let value_dict = {};
    const tagName = (element.tagName || '').toLowerCase();
    if (tagName === 'wa-switch' || tagName === 'wa-checkbox') {
        value_dict[element_id] = coerceBoolean(element.checked);
    } else if (tagName === 'input' && element.type === 'checkbox') {
        value_dict[element_id] = coerceBoolean(element.checked);
    } else {
        value_dict[element_id] = element.value;
    }
    send_ws({
        type: 'value_changed',
        values: value_dict,
        cake: current_cake
    });
}

function process_commands(commands) {
    commands.forEach(function(request) {
        let command = request["command"];
        let parameters = request["parameters"];
        if (command == "go_to") {
            go_to_cake(parameters['cake'], parameters['request']);
        }
        if (command == 'show_message') {
            show_messages([parameters["msg"]]);
        }
        if (command == 'refresh') {
            go_to_cake("_refresh_");
        }
        if (command == 'reload') {
            window.location.reload();
        }
    })
}

function check_revisions(updates) {
    let update_targets = [];
    if (updates['_root_'] != root_id) {
        window.location.reload();
        return;
    }
    for (let [element_id, value] of Object.entries(updates['_value_'])) {
        const element = document.getElementById(element_id);
        if (element) {
            const tagName = (element.tagName || '').toLowerCase();
            if (tagName === 'wa-switch' || tagName === 'wa-checkbox') {
                element.checked = coerceBoolean(value);
            } else if (tagName === 'input' && element.type === 'checkbox') {
                element.checked = coerceBoolean(value);
            } else {
                element.value = value;
            }
        }
    }
    for (let [element_id, value] of Object.entries(updates['_inner_html_'])) {
        const element = document.getElementById(element_id);
        if (element) {
            element.innerHTML = value;
        }
    }
    for (let [element_id, styles] of Object.entries(updates['_style_'])) {
        const element = document.getElementById(element_id);
        if (element) {
            for (let [key, value] of Object.entries(styles)) {
                if (value == "-") {
                    value = null;
                }
                element.style[key] = value;
            }
        }
    }
    for (let [element_id, styles] of Object.entries(updates['_attr_'])) {
        const element = document.getElementById(element_id);
        if (element) {
            for (let [key, value] of Object.entries(styles)) {
                if (value == "-") {
                    element.removeAttribute(key);
                } else {
                    element.setAttribute(key, value);
                }
            }
        }
    }
    delete updates['_root_'];
    delete updates['_value_'];
    delete updates['_inner_html_'];
    delete updates['_style_'];
    delete updates['_attr_'];
    for (let [topping_id, revision] of Object.entries(updates)) {
        if (revisions[topping_id] !== revision) {
            update_targets.push(topping_id);
        }
    }
    refresh(update_targets);
}

function refresh(update_targets) {
    if (update_targets.length == 0) return;
    send_ws({
        type: 'revision',
        targets: update_targets,
        cake: current_cake
    });
}

function apply_revision_payload(payload) {
    for (let [topping_id, content] of Object.entries(payload)) {
        const element = document.getElementById(topping_id);
        if (element) {
            element.innerHTML = content['content'];
            call_registered_function(content['function_call']);
        }
        revisions[topping_id] = content['revision'];
    }
    wait_indicator(false);
}

function call_registered_function(request) {
   request.forEach(function(fc) {
        let func = registered_functions[fc[0]];
        if( typeof (func) !== 'undefined' ) {
            func(fc[1]);
        }
    })
}

function call_post_rendering_functions() {
    post_rendering_functions.forEach(function(func) {
        func();
    });
 }

function apply_card_state() {
    const elements = document.getElementsByClassName("draggable");
    const num_elements = elements.length;
    for (let i = 0; i < num_elements; i++) {
        const element = elements[i];
        cardState.ensureVisibilityTracked(element);
        cardState.applyToElement(element);
    }
}

function go_to_cake(cake_name, request = {}) {
    if (cake_name == current_cake) return;
    if (cake_name == "_refresh_") {
        cake_name = current_cake
    }
    if (typeof (request) === 'undefined') { request = {}; }
    send_ws({
        type: 'go_to',
        cake: cake_name,
        request: request
    });
}

function apply_go_to_response(data) {
    let element = document.getElementById('container');
    if (element) {
        element.innerHTML = data['content'];
    }
    element = document.getElementById('floating_container');
    if (element) {
        element.innerHTML = data['floating_content'];
    }
    revisions = data['revisions'];
    current_cake = data['cake_name'] || data['cake'];
    call_registered_function(data['function_call']);
    call_post_rendering_functions();
    wait_indicator(false);
}

function wait_indicator(state) {
    change_visibility('wait_indicator', state);
}

function switch_card(element_id, action='switch') {
    const element = document.getElementById(element_id);
    if (element) {
        cardState.ensureVisibilityTracked(element);
        const state = cardState.getVisibility(element_id);
        const isVisible = (typeof state === 'boolean') ? state : element.style.display != 'none';
        if (action == 'get_state') {
            return isVisible
        }
        if (action == 'switch')
        {
            action = isVisible ? 'close' : 'open';
        }
        if (action == 'close' && isVisible) {
            document.activeElement.blur();
            element.style.display = 'none';
            cardState.setVisibility(element_id, false);
        }
        if (action == 'open' && !isVisible) {
            element.style.display = '';
            cardState.setVisibility(element_id, true);
        }
        if (element_id.endsWith('.honeycomb')) {
            const script_indicator = document.getElementById('script_indicator');
            if (script_indicator) {
                script_indicator.innerHTML = action == 'open' ? "&#11088;" : "&starf;";
            }
        }
    }
}

let pancake_state = {};
function save_state(key, state, lasting=False) {
    key = current_cake+"."+key;
    if(lasting) {
        localStorage.setItem("a", "Smith");
    }
}

function recall_state(key, state) {
    localStorage.setItem("lastname", "Smith");
}

function change_visibility(element_id, state='change') {
    const element = document.getElementById(element_id);
    if (element) {
        if(state == 'change') {state = element.style.display == 'none';}
        if (state) { element.style.display = ''; } else { element.style.display = 'none'; }
    }
}

function show_messages(msgs) {
    if (msgs.length == 0) return;
    const toast = document.getElementById("msg_box");
    msgs.forEach(function(msg) {toast.innerHTML = msg; toast.className = "show"; setTimeout(function(){ toast.className = toast.className.replace("show", ""); toast.innerHTML="";}, 3000);})
}

function close_dropdowns(except_id = null) {
    const dropdowns = document.getElementsByClassName("pk-dropdown");
    for (let i = 0; i < dropdowns.length; i++) {
        const el = dropdowns[i];
        if (except_id && el.id === except_id) continue;
        el.classList.remove("pk-open");
        const btn = el.querySelector("button[aria-expanded]");
        if (btn) btn.setAttribute("aria-expanded", "false");
    }
}

function toggle_dropdown(element_id, e) {
    if (e && typeof e.stopPropagation === "function") e.stopPropagation();
    const el = document.getElementById(element_id);
    if (!el) return;
    const isOpen = el.classList.contains("pk-open");
    close_dropdowns(element_id);
    el.classList.toggle("pk-open", !isOpen);
    const btn = el.querySelector("button[aria-expanded]");
    if (btn) btn.setAttribute("aria-expanded", (!isOpen).toString());
}

document.addEventListener("click", function() {
    close_dropdowns();
});

document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        close_dropdowns();
    }
});

function modified_click_handler(element_id, e) {
    if(!(e.ctrlKey || e.metaKey)) {
        return;
    }
    if(e.shiftKey) {
        selected_toppings.push(element_id);
    } else {
        selected_toppings = [element_id];
    }
    send_event(element_id, "select", selected_toppings);
    e.preventDefault();
}

function set_topping_click_with_modifier_key() {
    let elements = document.getElementsByClassName("topping");
    let num_elements = elements.length;
    selected_toppings = [];
    for(let i = 0; i < num_elements; i++) {
         let element = elements[i];
         element.addEventListener("mousedown", modified_click_handler.bind(this, element.id), false);
    }
}

register_post_rendering_function(apply_card_state);
register_post_rendering_function(set_topping_click_with_modifier_key);
init_socket();
