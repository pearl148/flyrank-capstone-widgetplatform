(function(){
    var script = document.currentScript;
    var src = new URL(script.src);
    var API = src.origin;
    var widgetId = src.searchParams.get("id");
    if(!widgetId){
        console.error("Widget: missing ?id= in script URL");
        return;
    }

    fetch(API + "/widgets/" + encodeURIComponent(widgetId) + "/config")
    .then(function(r){
        if(!r.ok) throw new Error("Config request failed: " + r.status);
        return r.json();
    })
    .then(function(config){
        render(config);
    })
    .catch(function(err){
        console.error("Widget failed to load:", err);
    });

    function render(config){
        const form = document.createElement("form");
        form.className = "widget";
        script.parentNode.insertBefore(form,script)
        const h3 = document.createElement("h3");
        h3.textContent = config.title;
        form.appendChild(h3);
        if(config.fields){
            Object.entries(config.fields).forEach(([name,def])=>{
                const fieldDiv = document.createElement('div');
                fieldDiv.className = "widget-field";
                const label = document.createElement('label');
                label.textContent = def.label;
                label.htmlFor = name;

                const input = document.createElement('input');
                input.type = def.type || 'text';
                input.name = name;
                const inputId = "w-" + widgetId + "-" + name;
                input.id = inputId;
                label.htmlFor = inputId;
                input.required = Boolean(def.required);

                fieldDiv.appendChild(label);
                fieldDiv.appendChild(input);
                form.appendChild(fieldDiv);

            });
        }

const button = document.createElement("button");
button.type = "submit";
button.textContent = config.button_text || "Submit";

const message = document.createElement("div");
message.className = "widget-response";

form.addEventListener("submit", function (e) {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  button.disabled = true;
  message.textContent = "";

  fetch(API + "/submissions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ widget_id: widgetId, data: data })
  })
    .then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (body) {
        if (r.ok) {
          form.reset();
          message.textContent = "Thanks!";
        } else if (typeof body.detail === "string") {
          message.textContent = body.detail;
        } else {
          message.textContent = "Please check your answers and try again.";
        }
      });
    })
    .catch(function () { message.textContent = "Could not send. Please try again."; })
    .finally(function () { button.disabled = false; });
});

form.appendChild(button);
form.appendChild(message);
    }
})();