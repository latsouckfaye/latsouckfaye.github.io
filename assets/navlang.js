(function(){
  var STORAGE_KEY = "site-lang";

  function applyLang(lang){
    document.documentElement.setAttribute("lang", lang);
    document.body.setAttribute("data-lang-ui", lang);

    document.querySelectorAll("[data-en]").forEach(function(el){
      if(lang === "en"){
        if(el.getAttribute("data-fr") === null){
          el.setAttribute("data-fr", el.textContent);
        }
        el.textContent = el.getAttribute("data-en");
      } else if(el.getAttribute("data-fr") !== null){
        el.textContent = el.getAttribute("data-fr");
      }
    });

    var titleHolder = document.querySelector("[data-title-en]");
    if(titleHolder){
      if(lang === "en"){
        if(!titleHolder.dataset.titleFr) titleHolder.dataset.titleFr = document.title;
        document.title = titleHolder.getAttribute("data-title-en");
      } else if(titleHolder.dataset.titleFr){
        document.title = titleHolder.dataset.titleFr;
      }
    }

    document.querySelectorAll(".navlang button").forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-lang") === lang);
    });
  }

  function inject(){
    var tools = document.querySelector(".quarto-navbar-tools");
    if(!tools || document.querySelector(".navlang")) return;
    var stored = (window.localStorage && localStorage.getItem(STORAGE_KEY)) || "fr";

    var wrap = document.createElement("div");
    wrap.className = "navlang";
    wrap.setAttribute("role", "group");
    wrap.setAttribute("aria-label", "Langue du site / Site language");
    wrap.innerHTML =
      "<button type=\"button\" data-lang=\"fr\" aria-pressed=\"" + (stored === "fr") + "\">FR</button>" +
      "<button type=\"button\" data-lang=\"en\" aria-pressed=\"" + (stored === "en") + "\">EN</button>";
    tools.insertBefore(wrap, tools.firstChild);

    wrap.querySelectorAll("button").forEach(function(b){
      b.addEventListener("click", function(){
        var lang = b.getAttribute("data-lang");
        if(window.localStorage) localStorage.setItem(STORAGE_KEY, lang);
        applyLang(lang);
      });
    });

    applyLang(stored);
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", inject);
  } else {
    inject();
  }
})();
