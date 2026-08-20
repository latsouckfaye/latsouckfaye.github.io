(function(){
  var PILLS = [
    {href:"/portfolio.html", icon:"bi-person-badge", shape:"circle", cls:"c-portfolio", label:"Portfolio", labelEn:"Portfolio"},
    {href:"/tutoriels.html", icon:"bi-journal-code", shape:"hexagon", cls:"c-tutoriels", label:"Tutoriels", labelEn:"Tutorials"},
    {href:"/blog.html", icon:"bi-pencil-square", shape:"pentagon", cls:"c-blog", label:"Blog", labelEn:"Blog"}
  ];

  function pillsHtml(lang){
    return PILLS.map(function(p){
      var text = lang === "en" ? p.labelEn : p.label;
      return "<a class=\"pillshape " + p.shape + " " + p.cls + "\" href=\"" + p.href + "\">" +
        "<span class=\"pillshapeinner\"><i class=\"bi " + p.icon + "\"></i><span data-en=\"" + p.labelEn + "\">" + text + "</span></span></a>";
    }).join("");
  }

  function injectBanner(anchor, lang){
    if(document.querySelector(".sitebanner")) return;
    if(document.querySelector(".herohome")) return;
    var banner = document.createElement("div");
    banner.className = "sitebanner";
    banner.innerHTML =
      "<p class=\"idtag\"><span class=\"idpunc\">&lt;</span><span class=\"idname\">Paul Faye</span> <span class=\"idattr\">role</span><span class=\"idpunc\">=</span><span class=\"idval\">&quot;Data scientist, Ph.D.&quot;</span><span class=\"idpunc\"> /&gt;</span></p>" +
      "<div class=\"pillarrow\">" + pillsHtml(lang) + "</div>";
    anchor.parentNode.insertBefore(banner, anchor);
  }

  function injectFooter(anchor, lang){
    if(document.querySelector(".sitefooter")) return;
    var codeLabel = lang === "en" ? "Notebook code under" : "Code des notebooks sous licence";
    var contentLabel = lang === "en" ? "Content (articles, tutorials) under" : "Contenu (articles, tutoriels) sous licence";
    var emailLabel = lang === "en" ? "Send an email" : "Envoyer un e-mail";
    var footer = document.createElement("div");
    footer.className = "sitefooter";
    footer.innerHTML =
      "<div class=\"contactrow\">" +
      "<a class=\"iconbtn ic-linkedin\" href=\"https://www.linkedin.com/in/paulalfaye\" target=\"_blank\" rel=\"noopener\" aria-label=\"LinkedIn\"><i class=\"bi bi-linkedin\"></i></a>" +
      "<a class=\"iconbtn ic-email\" id=\"sitefooterEmail\" href=\"#\" aria-label=\"" + emailLabel + "\"><i class=\"bi bi-envelope-at-fill\"></i></a>" +
      "<a class=\"iconbtn ic-github\" href=\"https://github.com/latsouckfaye\" target=\"_blank\" rel=\"noopener\" aria-label=\"GitHub\"><i class=\"bi bi-github\"></i></a>" +
      "</div>" +
      "<p class=\"licenseline\">© 2026 Paul Faye · <span data-en=\"Notebook code under\">" + codeLabel + "</span> <a href=\"https://opensource.org/licenses/MIT\" target=\"_blank\" rel=\"noopener\">MIT</a> · <span data-en=\"Content (articles, tutorials) under\">" + contentLabel + "</span> <a href=\"https://creativecommons.org/licenses/by-nc/4.0/\" target=\"_blank\" rel=\"noopener\">CC BY-NC 4.0</a></p>";
    anchor.parentNode.insertBefore(footer, anchor.nextSibling);
    var emailLink = footer.querySelector("#sitefooterEmail");
    var u = "paul.a.faye", d = "outlook.com";
    emailLink.href = "mailto:" + u + "@" + d;
  }

  function build(){
    var anchor = document.getElementById("quarto-content");
    if(!anchor || !anchor.parentNode) return;
    var lang = (window.localStorage && localStorage.getItem("site-lang")) || "fr";
    injectBanner(anchor, lang);
    injectFooter(anchor, lang);
  }

  if(document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
