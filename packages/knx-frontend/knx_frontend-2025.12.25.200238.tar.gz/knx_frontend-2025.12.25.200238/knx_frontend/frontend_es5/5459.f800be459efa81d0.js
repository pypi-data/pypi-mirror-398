"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5459"],{89600:function(t,e,r){r.a(t,(async function(t,e){try{var o=r(44734),n=r(56038),a=r(69683),i=r(25460),s=r(6454),c=r(62826),h=r(55262),p=r(96196),d=r(77845),l=t([h]);h=(l.then?(await l)():l)[0];var u,v=t=>t,y=function(t){function e(){return(0,o.A)(this,e),(0,a.A)(this,e,arguments)}return(0,s.A)(e,t),(0,n.A)(e,[{key:"updated",value:function(t){if((0,i.A)(e,"updated",this,3)([t]),t.has("size"))switch(this.size){case"tiny":this.style.setProperty("--ha-spinner-size","16px");break;case"small":this.style.setProperty("--ha-spinner-size","28px");break;case"medium":this.style.setProperty("--ha-spinner-size","48px");break;case"large":this.style.setProperty("--ha-spinner-size","68px");break;case void 0:this.style.removeProperty("--ha-progress-ring-size")}}}],[{key:"styles",get:function(){return[h.A.styles,(0,p.AH)(u||(u=v`
        :host {
          --indicator-color: var(
            --ha-spinner-indicator-color,
            var(--primary-color)
          );
          --track-color: var(--ha-spinner-divider-color, var(--divider-color));
          --track-width: 4px;
          --speed: 3.5s;
          font-size: var(--ha-spinner-size, 48px);
        }
      `))]}}])}(h.A);(0,c.__decorate)([(0,d.MZ)()],y.prototype,"size",void 0),y=(0,c.__decorate)([(0,d.EM)("ha-spinner")],y),e()}catch(f){e(f)}}))},54393:function(t,e,r){r.a(t,(async function(t,o){try{r.r(e);var n=r(44734),a=r(56038),i=r(69683),s=r(6454),c=(r(28706),r(62826)),h=r(96196),p=r(77845),d=r(5871),l=r(89600),u=(r(371),r(45397),r(39396)),v=t([l]);l=(v.then?(await v)():v)[0];var y,f,b,g,x,k,m=t=>t,_=function(t){function e(){var t;(0,n.A)(this,e);for(var r=arguments.length,o=new Array(r),a=0;a<r;a++)o[a]=arguments[a];return(t=(0,i.A)(this,e,[].concat(o))).noToolbar=!1,t.rootnav=!1,t.narrow=!1,t}return(0,s.A)(e,t),(0,a.A)(e,[{key:"render",value:function(){var t;return(0,h.qy)(y||(y=m`
      ${0}
      <div class="content">
        <ha-spinner></ha-spinner>
        ${0}
      </div>
    `),this.noToolbar?"":(0,h.qy)(f||(f=m`<div class="toolbar">
            ${0}
          </div>`),this.rootnav||null!==(t=history.state)&&void 0!==t&&t.root?(0,h.qy)(b||(b=m`
                  <ha-menu-button
                    .hass=${0}
                    .narrow=${0}
                  ></ha-menu-button>
                `),this.hass,this.narrow):(0,h.qy)(g||(g=m`
                  <ha-icon-button-arrow-prev
                    .hass=${0}
                    @click=${0}
                  ></ha-icon-button-arrow-prev>
                `),this.hass,this._handleBack)),this.message?(0,h.qy)(x||(x=m`<div id="loading-text">${0}</div>`),this.message):h.s6)}},{key:"_handleBack",value:function(){(0,d.O)()}}],[{key:"styles",get:function(){return[u.RF,(0,h.AH)(k||(k=m`
        :host {
          display: block;
          height: 100%;
          background-color: var(--primary-background-color);
        }
        .toolbar {
          display: flex;
          align-items: center;
          font-size: var(--ha-font-size-xl);
          height: var(--header-height);
          padding: 8px 12px;
          pointer-events: none;
          background-color: var(--app-header-background-color);
          font-weight: var(--ha-font-weight-normal);
          color: var(--app-header-text-color, white);
          border-bottom: var(--app-header-border-bottom, none);
          box-sizing: border-box;
        }
        @media (max-width: 599px) {
          .toolbar {
            padding: 4px;
          }
        }
        ha-menu-button,
        ha-icon-button-arrow-prev {
          pointer-events: auto;
        }
        .content {
          height: calc(100% - var(--header-height));
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }
        #loading-text {
          max-width: 350px;
          margin-top: 16px;
        }
      `))]}}])}(h.WF);(0,c.__decorate)([(0,p.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,c.__decorate)([(0,p.MZ)({type:Boolean,attribute:"no-toolbar"})],_.prototype,"noToolbar",void 0),(0,c.__decorate)([(0,p.MZ)({type:Boolean})],_.prototype,"rootnav",void 0),(0,c.__decorate)([(0,p.MZ)({type:Boolean})],_.prototype,"narrow",void 0),(0,c.__decorate)([(0,p.MZ)()],_.prototype,"message",void 0),_=(0,c.__decorate)([(0,p.EM)("hass-loading-screen")],_),o()}catch(w){o(w)}}))},74488:function(t,e,r){var o=r(67680),n=Math.floor,a=function(t,e){var r=t.length;if(r<8)for(var i,s,c=1;c<r;){for(s=c,i=t[c];s&&e(t[s-1],i)>0;)t[s]=t[--s];s!==c++&&(t[s]=i)}else for(var h=n(r/2),p=a(o(t,0,h),e),d=a(o(t,h),e),l=p.length,u=d.length,v=0,y=0;v<l||y<u;)t[v+y]=v<l&&y<u?e(p[v],d[y])<=0?p[v++]:d[y++]:v<l?p[v++]:d[y++];return t};t.exports=a},13709:function(t,e,r){var o=r(82839).match(/firefox\/(\d+)/i);t.exports=!!o&&+o[1]},13763:function(t,e,r){var o=r(82839);t.exports=/MSIE|Trident/.test(o)},3607:function(t,e,r){var o=r(82839).match(/AppleWebKit\/(\d+)\./);t.exports=!!o&&+o[1]},89429:function(t,e,r){var o=r(44576),n=r(38574);t.exports=function(t){if(n){try{return o.process.getBuiltinModule(t)}catch(e){}try{return Function('return require("'+t+'")')()}catch(e){}}}}}]);
//# sourceMappingURL=5459.f800be459efa81d0.js.map