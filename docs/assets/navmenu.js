(function(){
  var ITEMS = [
    {label:"À propos", labelEn:"About", href:"/index.html", icon:"bi-person-circle", cls:"c-apropos", main:true},
    {label:"Portfolio", labelEn:"Portfolio", href:"/portfolio.html", icon:"bi-person-badge", cls:"c-portfolio", main:true},
    {label:"Tutoriels", labelEn:"Tutorials", href:"/tutoriels.html", icon:"bi-journal-code", cls:"c-tutoriels", main:true},
    {label:"Blog", labelEn:"Blog", href:"/blog.html", icon:"bi-pencil-square", cls:"c-blog", main:true}
  ];
  var SUB = [
    {group:"Portfolio", groupEn:"Portfolio", cls:"c-portfolio", label:"Vue d'ensemble", labelEn:"Overview", href:"/portfolio.html"},
    {group:"Portfolio", groupEn:"Portfolio", cls:"c-portfolio", label:"Parcours", labelEn:"Career path", href:"/parcours.html"},
    {group:"Portfolio", groupEn:"Portfolio", cls:"c-portfolio", label:"Travaux", labelEn:"Work", href:"/projets.html"},
    {group:"Tutoriels publiés", groupEn:"Published tutorials", cls:"c-tutoriels", label:"Comparer des cartes à différentes résolutions", labelEn:"Comparing maps at different resolutions", href:"/tutoriels/comparer-cartes/comparer-cartes.html"},
    {group:"Tutoriels publiés", groupEn:"Published tutorials", cls:"c-tutoriels", label:"Méthodes d'échantillonnage stratégique", labelEn:"Strategic sampling methods", href:"/tutoriels/echantillonnage/echantillonnage.html"},
    {group:"Blog", groupEn:"Blog", cls:"c-blog", label:"Data & Tech", labelEn:"Data & Tech", href:"/blog.html#category=Data%20%26%20Tech"},
    {group:"Blog", groupEn:"Blog", cls:"c-blog", label:"Finance & Investissement", labelEn:"Finance & Investing", href:"/blog.html#category=Finance%20%26%20Investissement"},
    {group:"Blog", groupEn:"Blog", cls:"c-blog", label:"Projets & Build", labelEn:"Projects & Build", href:"/blog.html#category=Projets%20%26%20Build"}
  ];

  function build(){
    if(document.getElementById("navmenuOverlay")) return;

    var navContainer = document.querySelector(".navbar-container.container-fluid") || document.querySelector(".navbar-container");
    if(!navContainer) return;

    var lang = (window.localStorage && localStorage.getItem("site-lang")) || "fr";
    function t(fr, en){ return lang === "en" ? en : fr; }

    var trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "navmenu-trigger";
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-expanded", "false");
    trigger.setAttribute("aria-controls", "navmenuOverlay");
    trigger.setAttribute("aria-label", t("Ouvrir la navigation", "Open navigation"));
    trigger.innerHTML = "<span class=\"navmenu-bars\"><span></span><span></span><span></span></span>";
    navContainer.insertAdjacentElement("afterbegin", trigger);

    var overlay = document.createElement("div");
    overlay.className = "navmenu-overlay";
    overlay.id = "navmenuOverlay";
    overlay.setAttribute("aria-hidden", "true");

    var groupsHtml = "";
    var seen = {};
    SUB.forEach(function(s){ seen[s.group] = true; });
    Object.keys(seen).forEach(function(g){
      var first = SUB.filter(function(s){ return s.group === g; })[0];
      groupsHtml += "<div class=\"navmenu-subgroup\"><p class=\"navmenu-grouplabel " + first.cls + "\"><span class=\"navmenu-dot\"></span><span data-en=\"" + first.groupEn + "\">" + g + "</span></p>";
      SUB.filter(function(s){ return s.group === g; }).forEach(function(s){
        groupsHtml += "<a class=\"navmenu-sublink " + s.cls + "\" href=\"" + s.href + "\"><span data-en=\"" + s.labelEn + "\">" + s.label + "</span></a>";
      });
      groupsHtml += "</div>";
    });

    overlay.innerHTML =
      "<div class=\"navmenu-backdrop\" data-navmenu-close></div>" +
      "<div class=\"navmenu-panel\" role=\"dialog\" aria-modal=\"true\" aria-label=\"Navigation\">" +
      "<button type=\"button\" class=\"navmenu-close\" aria-label=\"" + t("Fermer", "Close") + "\" data-navmenu-close><i class=\"bi bi-x-lg\"></i></button>" +
      "<p class=\"navmenu-greeting\" data-en=\"Where do you want to go?\">Où veux-tu aller&nbsp;?</p>" +
      "<div class=\"navmenu-search\"><i class=\"bi bi-search\"></i><input type=\"text\" id=\"navmenuInput\" placeholder=\"" + t("Aller à…", "Go to…") + "\" autocomplete=\"off\" aria-label=\"" + t("Rechercher une page", "Search pages") + "\"></div>" +
      "<nav class=\"navmenu-main\">" +
      ITEMS.map(function(it){
        return "<a class=\"navmenu-link " + it.cls + "\" href=\"" + it.href + "\"><span class=\"navmenu-icon\"><i class=\"bi " + it.icon + "\"></i></span><span data-en=\"" + it.labelEn + "\">" + it.label + "</span></a>";
      }).join("") +
      "</nav>" +
      "<div class=\"navmenu-subgrid\">" + groupsHtml + "</div>" +
      "</div>";

    document.body.appendChild(overlay);

    var input = overlay.querySelector("#navmenuInput");
    var allLinks = overlay.querySelectorAll(".navmenu-link, .navmenu-sublink");
    var subgroups = overlay.querySelectorAll(".navmenu-subgroup");

    function openMenu(){
      overlay.classList.add("open");
      overlay.setAttribute("aria-hidden", "false");
      trigger.setAttribute("aria-expanded", "true");
      document.body.classList.add("navmenu-lock");
      setTimeout(function(){ input.focus(); }, 60);
    }
    function closeMenu(){
      overlay.classList.remove("open");
      overlay.setAttribute("aria-hidden", "true");
      trigger.setAttribute("aria-expanded", "false");
      document.body.classList.remove("navmenu-lock");
      input.value = "";
      filter("");
      trigger.focus();
    }
    function filter(q){
      q = q.trim().toLowerCase();
      allLinks.forEach(function(a){
        var match = !q || a.textContent.toLowerCase().indexOf(q) > -1;
        a.classList.toggle("navmenu-hidden", !match);
      });
      subgroups.forEach(function(g){
        var any = g.querySelectorAll(".navmenu-sublink:not(.navmenu-hidden)").length > 0;
        g.classList.toggle("navmenu-hidden", !any);
      });
    }

    trigger.addEventListener("click", function(){
      if(overlay.classList.contains("open")) closeMenu(); else openMenu();
    });
    overlay.querySelectorAll("[data-navmenu-close]").forEach(function(el){
      el.addEventListener("click", closeMenu);
    });
    document.addEventListener("keydown", function(e){
      if(e.key === "Escape" && overlay.classList.contains("open")) closeMenu();
    });
    input.addEventListener("input", function(){ filter(input.value); });
    input.addEventListener("keydown", function(e){
      if(e.key === "Enter"){
        var first = overlay.querySelector(".navmenu-link:not(.navmenu-hidden), .navmenu-sublink:not(.navmenu-hidden)");
        if(first) window.location.href = first.getAttribute("href");
      }
    });
    // Piège de focus minimal : Tab en fin de panneau revient au champ de recherche.
    overlay.addEventListener("keydown", function(e){
      if(e.key !== "Tab") return;
      var focusables = overlay.querySelectorAll("input, a:not(.navmenu-hidden), button");
      var list = Array.prototype.slice.call(focusables);
      if(list.length === 0) return;
      var first = list[0], last = list[list.length - 1];
      if(e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
      else if(!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
    });
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
