/*! For license information please see 8638.7af67fbc4bef5c2b.js.LICENSE.txt */
export const __webpack_id__="8638";export const __webpack_ids__=["8638"];export const __webpack_modules__={45845:function(t,e,i){var s=i(62826),n=i(77845),a=i(69162),o=i(47191);let r=class extends a.L{};r.styles=[o.R],r=(0,s.__decorate)([(0,n.EM)("mwc-checkbox")],r);var h=i(96196),d=i(94333),l=i(27686);class c extends l.J{render(){const t={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},e=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():h.qy``,s=this.hasMeta&&this.left?this.renderMeta():h.qy``,n=this.renderRipple();return h.qy`
      ${n}
      ${i}
      ${this.left?"":e}
      <span class=${(0,d.H)(t)}>
        <mwc-checkbox
            reducedTouchTarget
            tabindex=${this.tabindex}
            .checked=${this.selected}
            ?disabled=${this.disabled}
            @change=${this.onChange}>
        </mwc-checkbox>
      </span>
      ${this.left?e:""}
      ${s}`}async onChange(t){const e=t.target;this.selected===e.checked||(this._skipPropRequest=!0,this.selected=e.checked,await this.updateComplete,this._skipPropRequest=!1)}constructor(){super(...arguments),this.left=!1,this.graphic="control"}}(0,s.__decorate)([(0,n.P)("slot")],c.prototype,"slotElement",void 0),(0,s.__decorate)([(0,n.P)("mwc-checkbox")],c.prototype,"checkboxElement",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],c.prototype,"left",void 0),(0,s.__decorate)([(0,n.MZ)({type:String,reflect:!0})],c.prototype,"graphic",void 0);const p=h.AH`:host(:not([twoline])){height:56px}:host(:not([left])) .mdc-deprecated-list-item__meta{height:40px;width:40px}`;var m=i(7731),u=i(92542);i(70524);class g extends c{async onChange(t){super.onChange(t),(0,u.r)(this,t.type)}render(){const t={"mdc-deprecated-list-item__graphic":this.left,"mdc-deprecated-list-item__meta":!this.left},e=this.renderText(),i=this.graphic&&"control"!==this.graphic&&!this.left?this.renderGraphic():h.s6,s=this.hasMeta&&this.left?this.renderMeta():h.s6,n=this.renderRipple();return h.qy` ${n} ${i} ${this.left?"":e}
      <span class=${(0,d.H)(t)}>
        <ha-checkbox
          reducedTouchTarget
          tabindex=${this.tabindex}
          .checked=${this.selected}
          .indeterminate=${this.indeterminate}
          ?disabled=${this.disabled||this.checkboxDisabled}
          @change=${this.onChange}
        >
        </ha-checkbox>
      </span>
      ${this.left?e:""} ${s}`}constructor(...t){super(...t),this.checkboxDisabled=!1,this.indeterminate=!1}}g.styles=[m.R,p,h.AH`
      :host {
        --mdc-theme-secondary: var(--primary-color);
      }

      :host([graphic="avatar"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="medium"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="large"]) .mdc-deprecated-list-item__graphic,
      :host([graphic="control"]) .mdc-deprecated-list-item__graphic {
        margin-inline-end: var(--mdc-list-item-graphic-margin, 16px);
        margin-inline-start: 0px;
        direction: var(--direction);
      }
      .mdc-deprecated-list-item__meta {
        flex-shrink: 0;
        direction: var(--direction);
        margin-inline-start: auto;
        margin-inline-end: 0;
      }
      .mdc-deprecated-list-item__graphic {
        margin-top: var(--check-list-item-graphic-margin-top);
      }
      :host([graphic="icon"]) .mdc-deprecated-list-item__graphic {
        margin-inline-start: 0;
        margin-inline-end: var(--mdc-list-item-graphic-margin, 32px);
      }
    `],(0,s.__decorate)([(0,n.MZ)({type:Boolean,attribute:"checkbox-disabled"})],g.prototype,"checkboxDisabled",void 0),(0,s.__decorate)([(0,n.MZ)({type:Boolean})],g.prototype,"indeterminate",void 0),g=(0,s.__decorate)([(0,n.EM)("ha-check-list-item")],g)},35640:function(t,e,i){var s=i(62826),n=i(96196),a=i(77845);i(60961);class o extends n.WF{render(){return this.hass?n.qy`
      <ha-svg-icon .path=${"M12,2A7,7 0 0,1 19,9C19,11.38 17.81,13.47 16,14.74V17A1,1 0 0,1 15,18H9A1,1 0 0,1 8,17V14.74C6.19,13.47 5,11.38 5,9A7,7 0 0,1 12,2M9,21V20H15V21A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21M12,4A5,5 0 0,0 7,9C7,11.05 8.23,12.81 10,13.58V16H14V13.58C15.77,12.81 17,11.05 17,9A5,5 0 0,0 12,4Z"}></ha-svg-icon>
      <span class="prefix"
        >${this.hass.localize("ui.panel.config.tips.tip")}</span
      >
      <span class="text"><slot></slot></span>
    `:n.s6}}o.styles=n.AH`
    :host {
      display: block;
      text-align: center;
    }

    .text {
      direction: var(--direction);
      margin-left: 2px;
      margin-inline-start: 2px;
      margin-inline-end: initial;
      color: var(--secondary-text-color);
    }

    .prefix {
      font-weight: var(--ha-font-weight-medium);
    }
  `,(0,s.__decorate)([(0,a.MZ)({attribute:!1})],o.prototype,"hass",void 0),o=(0,s.__decorate)([(0,a.EM)("ha-tip")],o)},2909:function(t,e,i){i.a(t,(async function(t,s){try{i.r(e);var n=i(62826),a=i(81446),o=i(96196),r=i(77845),h=i(4937),d=i(92209),l=i(92542),c=i(79599),p=i(872),m=i(92001),u=i(9923),g=i(10234),_=i(39396),f=i(89473),y=(i(45845),i(95637),i(86451),i(75261),i(89600)),v=(i(60961),i(35640),i(16701)),b=i(11235),$=t([f,y,v,b]);[f,y,v,b]=$.then?(await $)():$;const x="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",w="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z";class k extends o.WF{showDialog(t){this._params=t,this._refreshMedia()}closeDialog(){this._filesChanged&&this._params.onClose&&this._params.onClose(),this._params=void 0,this._currentItem=void 0,this._uploading=!1,this._deleting=!1,this._filesChanged=!1,(0,l.r)(this,"dialog-closed",{dialog:this.localName})}render(){if(!this._params)return o.s6;const t=this._currentItem?.children?.filter((t=>!t.can_expand))||[];let e=0;return o.qy`
      <ha-dialog
        open
        scrimClickAction
        escapeKeyAction
        hideActions
        flexContent
        .heading=${this._params.currentItem.title}
        @closed=${this.closeDialog}
      >
        <ha-dialog-header slot="heading">
          ${0===this._selected.size?o.qy`
                <span slot="title">
                  ${this.hass.localize("ui.components.media-browser.file_management.title")}
                </span>

                <ha-media-upload-button
                  .disabled=${this._deleting}
                  .hass=${this.hass}
                  .currentItem=${this._params.currentItem}
                  @uploading=${this._startUploading}
                  @media-refresh=${this._doneUploading}
                  slot="actionItems"
                ></ha-media-upload-button>
                ${this._uploading?"":o.qy`
                      <ha-icon-button
                        .label=${this.hass.localize("ui.common.close")}
                        .path=${x}
                        dialogAction="close"
                        slot="navigationIcon"
                        dir=${(0,c.Vc)(this.hass)}
                      ></ha-icon-button>
                    `}
              `:o.qy`
                <ha-button
                  variant="danger"
                  slot="navigationIcon"
                  .disabled=${this._deleting}
                  @click=${this._handleDelete}
                >
                  <ha-svg-icon .path=${w} slot="start"></ha-svg-icon>
                  ${this.hass.localize("ui.components.media-browser.file_management."+(this._deleting?"deleting":"delete"),{count:this._selected.size})}
                </ha-button>

                ${this._deleting?"":o.qy`
                      <ha-button
                        slot="actionItems"
                        @click=${this._handleDeselectAll}
                      >
                        <ha-svg-icon
                          .path=${x}
                          slot="start"
                        ></ha-svg-icon>
                        ${this.hass.localize("ui.components.media-browser.file_management.deselect_all")}
                      </ha-button>
                    `}
              `}
        </ha-dialog-header>
        ${this._currentItem?t.length?o.qy`
                <ha-list multi @selected=${this._handleSelected}>
                  ${(0,h.u)(t,(t=>t.media_content_id),(t=>{const i=o.qy`
                        <ha-svg-icon
                          slot="graphic"
                          .path=${m.EC["directory"===t.media_class&&t.children_media_class||t.media_class].icon}
                        ></ha-svg-icon>
                      `;return o.qy`
                        <ha-check-list-item
                          ${(0,a.i0)({id:t.media_content_id,skipInitial:!0})}
                          graphic="icon"
                          .disabled=${this._uploading||this._deleting}
                          .selected=${this._selected.has(e++)}
                          .item=${t}
                        >
                          ${i} ${t.title}
                        </ha-check-list-item>
                      `}))}
                </ha-list>
              `:o.qy`<div class="no-items">
                <p>
                  ${this.hass.localize("ui.components.media-browser.file_management.no_items")}
                </p>
                ${this._currentItem?.children?.length?o.qy`<span class="folders"
                      >${this.hass.localize("ui.components.media-browser.file_management.folders_not_supported")}</span
                    >`:""}
              </div>`:o.qy`
              <div class="refresh">
                <ha-spinner></ha-spinner>
              </div>
            `}
        ${(0,d.x)(this.hass,"hassio")?o.qy`<ha-tip .hass=${this.hass}>
              ${this.hass.localize("ui.components.media-browser.file_management.tip_media_storage",{storage:o.qy`<a
                    href="/config/storage"
                    @click=${this.closeDialog}
                  >
                    ${this.hass.localize("ui.components.media-browser.file_management.tip_storage_panel")}</a
                  >`})}
            </ha-tip>`:o.s6}
      </ha-dialog>
    `}_handleSelected(t){this._selected=t.detail.index}_startUploading(){this._uploading=!0,this._filesChanged=!0}_doneUploading(){this._uploading=!1,this._refreshMedia()}_handleDeselectAll(){this._selected.size&&(this._selected=new Set)}async _handleDelete(){if(!(await(0,g.dk)(this,{text:this.hass.localize("ui.components.media-browser.file_management.confirm_delete",{count:this._selected.size}),warning:!0})))return;this._filesChanged=!0,this._deleting=!0;const t=[];let e=0;this._currentItem.children.forEach((i=>{i.can_expand||this._selected.has(e++)&&t.push(i)}));try{await Promise.all(t.map((async t=>{if((0,u.Jz)(t.media_content_id))await(0,u.WI)(this.hass,t.media_content_id);else if((0,u.iY)(t.media_content_id)){const e=(0,p.pD)(t.media_content_id);e&&await(0,p.vS)(this.hass,e)}this._currentItem={...this._currentItem,children:this._currentItem.children.filter((e=>e!==t))}})))}finally{this._deleting=!1,this._selected=new Set}}async _refreshMedia(){this._selected=new Set,this._currentItem=void 0,this._currentItem=await(0,u.Fn)(this.hass,this._params.currentItem.media_content_id)}static get styles(){return[_.nA,_.kO,o.AH`
        ha-dialog {
          --dialog-z-index: 9;
          --dialog-content-padding: 0;
        }

        @media (min-width: 800px) {
          ha-dialog {
            --mdc-dialog-max-width: 800px;
            --mdc-dialog-max-height: calc(
              100vh - var(--ha-space-18) - var(--safe-area-inset-y)
            );
          }
        }

        ha-dialog-header ha-media-upload-button,
        ha-dialog-header ha-button {
          --mdc-theme-primary: var(--primary-text-color);
          margin: 6px;
          display: block;
        }

        ha-tip {
          margin: 16px;
        }

        .refresh {
          display: flex;
          height: 200px;
          justify-content: center;
          align-items: center;
        }

        .no-items {
          text-align: center;
          padding: 16px;
        }
        .folders {
          color: var(--secondary-text-color);
          font-style: italic;
        }
      `]}constructor(...t){super(...t),this._uploading=!1,this._deleting=!1,this._selected=new Set,this._filesChanged=!1}}(0,n.__decorate)([(0,r.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,n.__decorate)([(0,r.wk)()],k.prototype,"_currentItem",void 0),(0,n.__decorate)([(0,r.wk)()],k.prototype,"_params",void 0),(0,n.__decorate)([(0,r.wk)()],k.prototype,"_uploading",void 0),(0,n.__decorate)([(0,r.wk)()],k.prototype,"_deleting",void 0),(0,n.__decorate)([(0,r.wk)()],k.prototype,"_selected",void 0),k=(0,n.__decorate)([(0,r.EM)("dialog-media-manage")],k),s()}catch(x){s(x)}}))},11235:function(t,e,i){i.a(t,(async function(t,e){try{var s=i(62826),n=i(96196),a=i(77845),o=i(92542),r=i(9923),h=i(10234),d=i(89473),l=(i(60961),t([d]));d=(l.then?(await l)():l)[0];const c="M9,16V10H5L12,3L19,10H15V16H9M5,20V18H19V20H5Z";class p extends n.WF{render(){return this.currentItem&&(0,r.Jz)(this.currentItem.media_content_id||"")?n.qy`
      <ha-button
        .disabled=${this._uploading>0}
        @click=${this._startUpload}
        .loading=${this._uploading>0}
      >
        <ha-svg-icon .path=${c} slot="start"></ha-svg-icon>
        ${this._uploading>0?this.hass.localize("ui.components.media-browser.file_management.uploading",{count:this._uploading}):this.hass.localize("ui.components.media-browser.file_management.add_media")}
      </ha-button>
    `:n.s6}async _startUpload(){if(this._uploading>0)return;const t=document.createElement("input");t.type="file",t.accept="audio/*,video/*,image/*",t.multiple=!0,t.addEventListener("change",(async()=>{(0,o.r)(this,"uploading");const e=t.files;document.body.removeChild(t);const i=this.currentItem.media_content_id;for(let t=0;t<e.length;t++){this._uploading=e.length-t;try{await(0,r.VA)(this.hass,i,e[t])}catch(s){(0,h.K$)(this,{text:this.hass.localize("ui.components.media-browser.file_management.upload_failed",{reason:s.message||s})});break}}this._uploading=0,(0,o.r)(this,"media-refresh")}),{once:!0}),t.style.display="none",document.body.append(t),t.click()}constructor(...t){super(...t),this._uploading=0}}(0,s.__decorate)([(0,a.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,s.__decorate)([(0,a.MZ)({attribute:!1})],p.prototype,"currentItem",void 0),(0,s.__decorate)([(0,a.wk)()],p.prototype,"_uploading",void 0),p=(0,s.__decorate)([(0,a.EM)("ha-media-upload-button")],p),e()}catch(c){e(c)}}))},81446:function(t,e,i){i.d(e,{i0:()=>y});var s=i(5055),n=i(42017),a=i(40054);const o=new WeakMap;let r=0;const h=new Map,d=new WeakSet,l=()=>new Promise((t=>requestAnimationFrame(t))),c=(t,e)=>{const i=t-e;return 0===i?void 0:i},p=(t,e)=>{const i=t/e;return 1===i?void 0:i},m={left:(t,e)=>{const i=c(t,e);return{value:i,transform:null==i||isNaN(i)?void 0:`translateX(${i}px)`}},top:(t,e)=>{const i=c(t,e);return{value:i,transform:null==i||isNaN(i)?void 0:`translateY(${i}px)`}},width:(t,e)=>{let i;0===e&&(e=1,i={width:"1px"});const s=p(t,e);return{value:s,overrideFrom:i,transform:null==s||isNaN(s)?void 0:`scaleX(${s})`}},height:(t,e)=>{let i;0===e&&(e=1,i={height:"1px"});const s=p(t,e);return{value:s,overrideFrom:i,transform:null==s||isNaN(s)?void 0:`scaleY(${s})`}}},u={duration:333,easing:"ease-in-out"},g=["left","top","width","height","opacity","color","background"],_=new WeakMap;class f extends a.Kq{createFinished(){this.resolveFinished?.(),this.finished=new Promise((t=>{this.l=t}))}async resolveFinished(){this.l?.(),this.l=void 0}render(t){return s.s6}getController(){return o.get(this.u)}isDisabled(){return this.options.disabled||this.getController()?.disabled}update(t,[e]){const i=void 0===this.u;return i&&(this.u=t.options?.host,this.u.addController(this),this.u.updateComplete.then((t=>this.t=!0)),this.element=t.element,_.set(this.element,this)),this.optionsOrCallback=e,(i||"function"!=typeof e)&&this.p(e),this.render(e)}p(t){t=t??{};const e=this.getController();void 0!==e&&((t={...e.defaultOptions,...t}).keyframeOptions={...e.defaultOptions.keyframeOptions,...t.keyframeOptions}),t.properties??=g,this.options=t}m(){const t={},e=this.element.getBoundingClientRect(),i=getComputedStyle(this.element);return this.options.properties.forEach((s=>{const n=e[s]??(m[s]?void 0:i[s]),a=Number(n);t[s]=isNaN(a)?n+"":a})),t}v(){let t,e=!0;return this.options.guard&&(t=this.options.guard(),e=((t,e)=>{if(Array.isArray(t)){if(Array.isArray(e)&&e.length===t.length&&t.every(((t,i)=>t===e[i])))return!1}else if(e===t)return!1;return!0})(t,this._)),this.h=this.t&&!this.isDisabled()&&!this.isAnimating()&&e&&this.element.isConnected,this.h&&(this._=Array.isArray(t)?Array.from(t):t),this.h}hostUpdate(){"function"==typeof this.optionsOrCallback&&this.p(this.optionsOrCallback()),this.v()&&(this.A=this.m(),this.i=this.i??this.element.parentNode,this.o=this.element.nextSibling)}async hostUpdated(){if(!this.h||!this.element.isConnected||this.options.skipInitial&&!this.isHostRendered)return;let t;this.prepare(),await l;const e=this.O(),i=this.j(this.options.keyframeOptions,e),s=this.m();if(void 0!==this.A){const{from:i,to:n}=this.N(this.A,s,e);this.log("measured",[this.A,s,i,n]),t=this.calculateKeyframes(i,n)}else{const i=h.get(this.options.inId);if(i){h.delete(this.options.inId);const{from:n,to:a}=this.N(i,s,e);t=this.calculateKeyframes(n,a),t=this.options.in?[{...this.options.in[0],...t[0]},...this.options.in.slice(1),t[1]]:t,r++,t.forEach((t=>t.zIndex=r))}else this.options.in&&(t=[...this.options.in,{}])}this.animate(t,i)}resetStyles(){void 0!==this.P&&(this.element.setAttribute("style",this.P??""),this.P=void 0)}commitStyles(){this.P=this.element.getAttribute("style"),this.webAnimation?.commitStyles(),this.webAnimation?.cancel()}reconnected(){}async disconnected(){if(!this.h)return;if(void 0!==this.options.id&&h.set(this.options.id,this.A),void 0===this.options.out)return;if(this.prepare(),await l(),this.i?.isConnected){const t=this.o&&this.o.parentNode===this.i?this.o:null;if(this.i.insertBefore(this.element,t),this.options.stabilizeOut){const t=this.m();this.log("stabilizing out");const e=this.A.left-t.left,i=this.A.top-t.top;!("static"===getComputedStyle(this.element).position)||0===e&&0===i||(this.element.style.position="relative"),0!==e&&(this.element.style.left=e+"px"),0!==i&&(this.element.style.top=i+"px")}}const t=this.j(this.options.keyframeOptions);await this.animate(this.options.out,t),this.element.remove()}prepare(){this.createFinished()}start(){this.options.onStart?.(this)}didFinish(t){t&&this.options.onComplete?.(this),this.A=void 0,this.animatingProperties=void 0,this.frames=void 0,this.resolveFinished()}O(){const t=[];for(let e=this.element.parentNode;e;e=e?.parentNode){const i=_.get(e);i&&!i.isDisabled()&&i&&t.push(i)}return t}get isHostRendered(){const t=d.has(this.u);return t||this.u.updateComplete.then((()=>{d.add(this.u)})),t}j(t,e=this.O()){const i={...u};return e.forEach((t=>Object.assign(i,t.options.keyframeOptions))),Object.assign(i,t),i}N(t,e,i){t={...t},e={...e};const s=i.map((t=>t.animatingProperties)).filter((t=>void 0!==t));let n=1,a=1;return s.length>0&&(s.forEach((t=>{t.width&&(n/=t.width),t.height&&(a/=t.height)})),void 0!==t.left&&void 0!==e.left&&(t.left=n*t.left,e.left=n*e.left),void 0!==t.top&&void 0!==e.top&&(t.top=a*t.top,e.top=a*e.top)),{from:t,to:e}}calculateKeyframes(t,e,i=!1){const s={},n={};let a=!1;const o={};for(const r in e){const i=t[r],h=e[r];if(r in m){const t=m[r];if(void 0===i||void 0===h)continue;const e=t(i,h);void 0!==e.transform&&(o[r]=e.value,a=!0,s.transform=`${s.transform??""} ${e.transform}`,void 0!==e.overrideFrom&&Object.assign(s,e.overrideFrom))}else i!==h&&void 0!==i&&void 0!==h&&(a=!0,s[r]=i,n[r]=h)}return s.transformOrigin=n.transformOrigin=i?"center center":"top left",this.animatingProperties=o,a?[s,n]:void 0}async animate(t,e=this.options.keyframeOptions){this.start(),this.frames=t;let i=!1;if(!this.isAnimating()&&!this.isDisabled()&&(this.options.onFrames&&(this.frames=t=this.options.onFrames(this),this.log("modified frames",t)),void 0!==t)){this.log("animate",[t,e]),i=!0,this.webAnimation=this.element.animate(t,e);const s=this.getController();s?.add(this);try{await this.webAnimation.finished}catch(t){}s?.remove(this)}return this.didFinish(i),i}isAnimating(){return"running"===this.webAnimation?.playState||this.webAnimation?.pending}log(t,e){this.shouldLog&&!this.isDisabled()&&console.log(t,this.options.id,e)}constructor(t){if(super(t),this.t=!1,this.i=null,this.o=null,this.h=!0,this.shouldLog=!1,t.type===n.OA.CHILD)throw Error("The `animate` directive must be used in attribute position.");this.createFinished()}}const y=(0,n.u$)(f),v=["top","right","bottom","left"];class b extends a.Kq{render(t,e){return s.s6}update(t,[e,i]){return void 0===this.u&&(this.u=t.options?.host,this.u.addController(this)),this.S=t.element,this.C=e,this.F=i??["left","top","width","height"],this.render(e,i)}hostUpdated(){this.$()}$(){const t="function"==typeof this.C?this.C():this.C?.value,e=t.offsetParent;if(void 0===t||!e)return;const i=t.getBoundingClientRect(),s=e.getBoundingClientRect();this.F?.forEach((t=>{const e=v.includes(t)?i[t]-s[t]:i[t];this.S.style[t]=e+"px"}))}constructor(t){if(super(t),t.type!==n.OA.ELEMENT)throw Error("The `position` directive must be used in attribute position.")}}(0,n.u$)(b)}};
//# sourceMappingURL=8638.7af67fbc4bef5c2b.js.map