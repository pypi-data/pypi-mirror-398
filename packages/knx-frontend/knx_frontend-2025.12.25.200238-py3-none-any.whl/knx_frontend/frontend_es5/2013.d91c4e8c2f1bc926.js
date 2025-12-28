"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["2013"],{99793:function(e,t,a){var n,o=a(96196);t.A=(0,o.AH)(n||(n=(e=>e)`:host {
  --width: 31rem;
  --spacing: var(--wa-space-l);
  --show-duration: 200ms;
  --hide-duration: 200ms;
  display: none;
}
:host([open]) {
  display: block;
}
.dialog {
  display: flex;
  flex-direction: column;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  width: var(--width);
  max-width: calc(100% - var(--wa-space-2xl));
  max-height: calc(100% - var(--wa-space-2xl));
  background-color: var(--wa-color-surface-raised);
  border-radius: var(--wa-panel-border-radius);
  border: none;
  box-shadow: var(--wa-shadow-l);
  padding: 0;
  margin: auto;
}
.dialog.show {
  animation: show-dialog var(--show-duration) ease;
}
.dialog.show::backdrop {
  animation: show-backdrop var(--show-duration, 200ms) ease;
}
.dialog.hide {
  animation: show-dialog var(--hide-duration) ease reverse;
}
.dialog.hide::backdrop {
  animation: show-backdrop var(--hide-duration, 200ms) ease reverse;
}
.dialog.pulse {
  animation: pulse 250ms ease;
}
.dialog:focus {
  outline: none;
}
@media screen and (max-width: 420px) {
  .dialog {
    max-height: 80vh;
  }
}
.open {
  display: flex;
  opacity: 1;
}
.header {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: nowrap;
  padding-inline-start: var(--spacing);
  padding-block-end: 0;
  padding-inline-end: calc(var(--spacing) - var(--wa-form-control-padding-block));
  padding-block-start: calc(var(--spacing) - var(--wa-form-control-padding-block));
}
.title {
  align-self: center;
  flex: 1 1 auto;
  font-family: inherit;
  font-size: var(--wa-font-size-l);
  font-weight: var(--wa-font-weight-heading);
  line-height: var(--wa-line-height-condensed);
  margin: 0;
}
.header-actions {
  align-self: start;
  display: flex;
  flex-shrink: 0;
  flex-wrap: wrap;
  justify-content: end;
  gap: var(--wa-space-2xs);
  padding-inline-start: var(--spacing);
}
.header-actions wa-button,
.header-actions ::slotted(wa-button) {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
}
.body {
  flex: 1 1 auto;
  display: block;
  padding: var(--spacing);
  overflow: auto;
  -webkit-overflow-scrolling: touch;
}
.body:focus {
  outline: none;
}
.body:focus-visible {
  outline: var(--wa-focus-ring);
  outline-offset: var(--wa-focus-ring-offset);
}
.footer {
  flex: 0 0 auto;
  display: flex;
  flex-wrap: wrap;
  gap: var(--wa-space-xs);
  justify-content: end;
  padding: var(--spacing);
  padding-block-start: 0;
}
.footer ::slotted(wa-button:not(:first-of-type)) {
  margin-inline-start: var(--wa-spacing-xs);
}
.dialog::backdrop {
  background-color: var(--wa-color-overlay-modal, rgb(0 0 0 / 0.25));
}
@keyframes pulse {
  0% {
    scale: 1;
  }
  50% {
    scale: 1.02;
  }
  100% {
    scale: 1;
  }
}
@keyframes show-dialog {
  from {
    opacity: 0;
    scale: 0.8;
  }
  to {
    opacity: 1;
    scale: 1;
  }
}
@keyframes show-backdrop {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
@media (forced-colors: active) {
  .dialog {
    border: solid 1px white;
  }
}
`))},93900:function(e,t,a){a.a(e,(async function(e,t){try{var n=a(78261),o=a(61397),i=a(50264),r=a(44734),s=a(56038),l=a(69683),c=a(6454),d=a(25460),u=(a(27495),a(90906),a(96196)),h=a(77845),p=a(94333),f=a(32288),g=a(17051),w=a(42462),m=a(28438),v=a(98779),b=a(27259),y=a(31247),k=a(97039),A=a(92070),x=a(9395),E=a(32510),C=a(17060),L=a(88496),D=a(99793),q=e([L,C]);[L,C]=q.then?(await q)():q;var $,O,P,M=e=>e,S=Object.defineProperty,U=Object.getOwnPropertyDescriptor,Z=(e,t,a,n)=>{for(var o,i=n>1?void 0:n?U(t,a):t,r=e.length-1;r>=0;r--)(o=e[r])&&(i=(n?o(t,a,i):o(i))||i);return n&&i&&S(t,a,i),i},z=function(e){function t(){var e;return(0,r.A)(this,t),(e=(0,l.A)(this,t,arguments)).localize=new C.c(e),e.hasSlotController=new A.X(e,"footer","header-actions","label"),e.open=!1,e.label="",e.withoutHeader=!1,e.lightDismiss=!1,e.handleDocumentKeyDown=t=>{"Escape"===t.key&&e.open&&(t.preventDefault(),t.stopPropagation(),e.requestClose(e.dialog))},e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"firstUpdated",value:function(){this.open&&(this.addOpenListeners(),this.dialog.showModal(),(0,k.JG)(this))}},{key:"disconnectedCallback",value:function(){(0,d.A)(t,"disconnectedCallback",this,3)([]),(0,k.I7)(this),this.removeOpenListeners()}},{key:"requestClose",value:(h=(0,i.A)((0,o.A)().m((function e(t){var a,n;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(a=new m.L({source:t}),this.dispatchEvent(a),!a.defaultPrevented){e.n=1;break}return this.open=!0,(0,b.Ud)(this.dialog,"pulse"),e.a(2);case 1:return this.removeOpenListeners(),e.n=2,(0,b.Ud)(this.dialog,"hide");case 2:this.open=!1,this.dialog.close(),(0,k.I7)(this),"function"==typeof(null==(n=this.originalTrigger)?void 0:n.focus)&&setTimeout((()=>n.focus())),this.dispatchEvent(new g.Z);case 3:return e.a(2)}}),e,this)}))),function(e){return h.apply(this,arguments)})},{key:"addOpenListeners",value:function(){document.addEventListener("keydown",this.handleDocumentKeyDown)}},{key:"removeOpenListeners",value:function(){document.removeEventListener("keydown",this.handleDocumentKeyDown)}},{key:"handleDialogCancel",value:function(e){e.preventDefault(),this.dialog.classList.contains("hide")||e.target!==this.dialog||this.requestClose(this.dialog)}},{key:"handleDialogClick",value:function(e){var t=e.target.closest('[data-dialog="close"]');t&&(e.stopPropagation(),this.requestClose(t))}},{key:"handleDialogPointerDown",value:(n=(0,i.A)((0,o.A)().m((function e(t){return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(t.target!==this.dialog){e.n=2;break}if(!this.lightDismiss){e.n=1;break}this.requestClose(this.dialog),e.n=2;break;case 1:return e.n=2,(0,b.Ud)(this.dialog,"pulse");case 2:return e.a(2)}}),e,this)}))),function(e){return n.apply(this,arguments)})},{key:"handleOpenChange",value:function(){this.open&&!this.dialog.open?this.show():!this.open&&this.dialog.open&&(this.open=!0,this.requestClose(this.dialog))}},{key:"show",value:(a=(0,i.A)((0,o.A)().m((function e(){var t;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:if(t=new v.k,this.dispatchEvent(t),!t.defaultPrevented){e.n=1;break}return this.open=!1,e.a(2);case 1:return this.addOpenListeners(),this.originalTrigger=document.activeElement,this.open=!0,this.dialog.showModal(),(0,k.JG)(this),requestAnimationFrame((()=>{var e=this.querySelector("[autofocus]");e&&"function"==typeof e.focus?e.focus():this.dialog.focus()})),e.n=2,(0,b.Ud)(this.dialog,"show");case 2:this.dispatchEvent(new w.q);case 3:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"render",value:function(){var e,t=!this.withoutHeader,a=this.hasSlotController.test("footer");return(0,u.qy)($||($=M`
      <dialog
        aria-labelledby=${0}
        aria-describedby=${0}
        part="dialog"
        class=${0}
        @cancel=${0}
        @click=${0}
        @pointerdown=${0}
      >
        ${0}

        <div part="body" class="body"><slot></slot></div>

        ${0}
      </dialog>
    `),null!==(e=this.ariaLabelledby)&&void 0!==e?e:"title",(0,f.J)(this.ariaDescribedby),(0,p.H)({dialog:!0,open:this.open}),this.handleDialogCancel,this.handleDialogClick,this.handleDialogPointerDown,t?(0,u.qy)(O||(O=M`
              <header part="header" class="header">
                <h2 part="title" class="title" id="title">
                  <!-- If there's no label, use an invisible character to prevent the header from collapsing -->
                  <slot name="label"> ${0} </slot>
                </h2>
                <div part="header-actions" class="header-actions">
                  <slot name="header-actions"></slot>
                  <wa-button
                    part="close-button"
                    exportparts="base:close-button__base"
                    class="close"
                    appearance="plain"
                    @click="${0}"
                  >
                    <wa-icon
                      name="xmark"
                      label=${0}
                      library="system"
                      variant="solid"
                    ></wa-icon>
                  </wa-button>
                </div>
              </header>
            `),this.label.length>0?this.label:String.fromCharCode(8203),(e=>this.requestClose(e.target)),this.localize.term("close")):"",a?(0,u.qy)(P||(P=M`
              <footer part="footer" class="footer">
                <slot name="footer"></slot>
              </footer>
            `)):"")}}]);var a,n,h}(E.A);z.css=D.A,Z([(0,h.P)(".dialog")],z.prototype,"dialog",2),Z([(0,h.MZ)({type:Boolean,reflect:!0})],z.prototype,"open",2),Z([(0,h.MZ)({reflect:!0})],z.prototype,"label",2),Z([(0,h.MZ)({attribute:"without-header",type:Boolean,reflect:!0})],z.prototype,"withoutHeader",2),Z([(0,h.MZ)({attribute:"light-dismiss",type:Boolean})],z.prototype,"lightDismiss",2),Z([(0,h.MZ)({attribute:"aria-labelledby"})],z.prototype,"ariaLabelledby",2),Z([(0,h.MZ)({attribute:"aria-describedby"})],z.prototype,"ariaDescribedby",2),Z([(0,x.w)("open",{waitUntilFirstUpdate:!0})],z.prototype,"handleOpenChange",1),z=Z([(0,h.EM)("wa-dialog")],z),document.addEventListener("click",(e=>{var t=e.target.closest("[data-dialog]");if(t instanceof Element){var a=(0,y.v)(t.getAttribute("data-dialog")||""),o=(0,n.A)(a,2),i=o[0],r=o[1];if("open"===i&&null!=r&&r.length){var s=t.getRootNode().getElementById(r);"wa-dialog"===(null==s?void 0:s.localName)?s.open=!0:console.warn(`A dialog with an ID of "${r}" could not be found in this document.`)}}})),u.S$||document.addEventListener("pointerdown",(()=>{})),t()}catch(I){t(I)}}))},17051:function(e,t,a){a.d(t,{Z:function(){return s}});var n=a(56038),o=a(44734),i=a(69683),r=a(6454),s=function(e){function t(){return(0,o.A)(this,t),(0,i.A)(this,t,["wa-after-hide",{bubbles:!0,cancelable:!1,composed:!0}])}return(0,r.A)(t,e),(0,n.A)(t)}((0,a(79993).A)(Event))},42462:function(e,t,a){a.d(t,{q:function(){return s}});var n=a(56038),o=a(44734),i=a(69683),r=a(6454),s=function(e){function t(){return(0,o.A)(this,t),(0,i.A)(this,t,["wa-after-show",{bubbles:!0,cancelable:!1,composed:!0}])}return(0,r.A)(t,e),(0,n.A)(t)}((0,a(79993).A)(Event))},28438:function(e,t,a){a.d(t,{L:function(){return s}});var n=a(56038),o=a(44734),i=a(69683),r=a(6454),s=function(e){function t(e){var a;return(0,o.A)(this,t),(a=(0,i.A)(this,t,["wa-hide",{bubbles:!0,cancelable:!0,composed:!0}])).detail=e,a}return(0,r.A)(t,e),(0,n.A)(t)}((0,a(79993).A)(Event))},98779:function(e,t,a){a.d(t,{k:function(){return s}});var n=a(56038),o=a(44734),i=a(69683),r=a(6454),s=function(e){function t(){return(0,o.A)(this,t),(0,i.A)(this,t,["wa-show",{bubbles:!0,cancelable:!0,composed:!0}])}return(0,r.A)(t,e),(0,n.A)(t)}((0,a(79993).A)(Event))},27259:function(e,t,a){a.d(t,{E9:function(){return l},Ud:function(){return s},i0:function(){return i}});var n=a(61397),o=a(50264);a(25276),a(26099),a(3362),a(38781);function i(e,t,a){return r.apply(this,arguments)}function r(){return(r=(0,o.A)((0,n.A)().m((function e(t,a,o){return(0,n.A)().w((function(e){for(;;)if(0===e.n)return e.a(2,t.animate(a,o).finished.catch((()=>{})))}),e)})))).apply(this,arguments)}function s(e,t){return new Promise((a=>{var n=new AbortController,o=n.signal;if(!e.classList.contains(t)){e.classList.remove(t),e.classList.add(t);var i=()=>{e.classList.remove(t),a(),n.abort()};e.addEventListener("animationend",i,{once:!0,signal:o}),e.addEventListener("animationcancel",i,{once:!0,signal:o})}}))}function l(e){return(e=e.toString().toLowerCase()).indexOf("ms")>-1?parseFloat(e)||0:e.indexOf("s")>-1?1e3*(parseFloat(e)||0):parseFloat(e)||0}},31247:function(e,t,a){a.d(t,{v:function(){return n}});a(2008),a(62062),a(18111),a(22489),a(61701),a(26099),a(42762);function n(e){return e.split(" ").map((e=>e.trim())).filter((e=>""!==e))}},97039:function(e,t,a){a.d(t,{I7:function(){return i},JG:function(){return o}});a(23792),a(2892),a(26099),a(27495),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(25440),a(62953);var n=new Set;function o(e){if(n.add(e),!document.documentElement.classList.contains("wa-scroll-lock")){var t=(i=document.documentElement.clientWidth,Math.abs(window.innerWidth-i)+(o=Number(getComputedStyle(document.body).paddingRight.replace(/px/,"")),isNaN(o)||!o?0:o)),a=getComputedStyle(document.documentElement).scrollbarGutter;a&&"auto"!==a||(a="stable"),t<2&&(a=""),document.documentElement.style.setProperty("--wa-scroll-lock-gutter",a),document.documentElement.classList.add("wa-scroll-lock"),document.documentElement.style.setProperty("--wa-scroll-lock-size",`${t}px`)}var o,i}function i(e){n.delete(e),0===n.size&&(document.documentElement.classList.remove("wa-scroll-lock"),document.documentElement.style.removeProperty("--wa-scroll-lock-size"))}}}]);
//# sourceMappingURL=2013.d91c4e8c2f1bc926.js.map