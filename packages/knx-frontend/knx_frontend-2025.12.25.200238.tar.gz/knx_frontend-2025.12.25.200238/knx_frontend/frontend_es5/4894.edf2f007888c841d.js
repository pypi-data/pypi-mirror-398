"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["4894"],{37445:function(e,t,a){var o,l,i,r,n,c,d,s,h,u,_,p,m,b,f,v,g,y,w=a(61397),x=a(50264),k=a(94741),C=a(78261),R=a(44734),A=a(56038),$=a(75864),L=a(69683),M=a(6454),D=a(25460),S=(a(28706),a(2008),a(50113),a(48980),a(74423),a(25276),a(23792),a(62062),a(44114),a(72712),a(26910),a(54554),a(18111),a(22489),a(20116),a(7588),a(61701),a(18237),a(13579),a(5506),a(26099),a(16034),a(3362),a(31415),a(17642),a(58004),a(33853),a(45876),a(32475),a(15024),a(31698),a(42762),a(46058),a(23500),a(62953),a(62826)),Z=a(34271),z=a(96196),H=a(77845),I=a(94333),O=a(32288),q=a(29485),T=a(22786),G=a(39501),F=a(92542),W=a(25749),E=a(40404),B=a(31432),P=(e,t)=>{var a,o={},l=(0,B.A)(e);try{for(l.s();!(a=l.n()).done;){var i=a.value,r=t(i);r in o?o[r].push(i):o[r]=[i]}}catch(n){l.e(n)}finally{l.f()}return o},U=a(39396),j=a(84183),V=(a(70524),a(60961),a(17262),a(3296),a(27208),a(48408),a(14603),a(47566),a(98721),a(2209)),N=()=>(o||(o=(0,V.LV)(new Worker(new URL(a.p+a.u("4346"),a.b)))),o),J=(e,t,a,o,l)=>N().sortData(e,t,a,o,l),K=a(99034),Y=e=>e,Q="zzzzz_undefined",X=function(e){function t(){var e;(0,R.A)(this,t);for(var a=arguments.length,o=new Array(a),_=0;_<a;_++)o[_]=arguments[_];return(e=(0,L.A)(this,t,[].concat(o))).narrow=!1,e.columns={},e.data=[],e.selectable=!1,e.clickable=!1,e.hasFab=!1,e.autoHeight=!1,e.id="id",e.noLabelFloat=!1,e.filter="",e.sortDirection=null,e._filterable=!1,e._filter="",e._filteredData=[],e._headerHeight=0,e._collapsedGroups=[],e._lastSelectedRowId=null,e._checkedRows=[],e._sortColumns={},e._curRequest=0,e._lastUpdate=0,e._debounceSearch=(0,E.s)((t=>{e._filter=t}),100,!1),e._sortedColumns=(0,T.A)(((e,t)=>t&&t.length?Object.keys(e).sort(((e,a)=>{var o=t.indexOf(e),l=t.indexOf(a);if(o!==l){if(-1===o)return 1;if(-1===l)return-1}return o-l})).reduce(((t,a)=>(t[a]=e[a],t)),{}):e)),e._keyFunction=t=>(null==t?void 0:t[e.id])||t,e._renderRow=(t,a,o,u)=>o?o.append?(0,z.qy)(l||(l=Y`<div class="mdc-data-table__row">${0}</div>`),o.content):o.empty?(0,z.qy)(i||(i=Y`<div class="mdc-data-table__row empty-row"></div>`)):(0,z.qy)(r||(r=Y`
      <div
        aria-rowindex=${0}
        role="row"
        .rowId=${0}
        @click=${0}
        class="mdc-data-table__row ${0}"
        aria-selected=${0}
        .selectable=${0}
      >
        ${0}
        ${0}
      </div>
    `),u+2,o[e.id],e._handleRowClick,(0,I.H)({"mdc-data-table__row--selected":e._checkedRows.includes(String(o[e.id])),clickable:e.clickable}),(0,O.J)(!!e._checkedRows.includes(String(o[e.id]))||void 0),!1!==o.selectable,e.selectable?(0,z.qy)(n||(n=Y`
              <div
                class="mdc-data-table__cell mdc-data-table__cell--checkbox"
                role="cell"
              >
                <ha-checkbox
                  class="mdc-data-table__row-checkbox"
                  @click=${0}
                  .rowId=${0}
                  .disabled=${0}
                  .checked=${0}
                >
                </ha-checkbox>
              </div>
            `),e._handleRowCheckboxClicked,o[e.id],!1===o.selectable,e._checkedRows.includes(String(o[e.id]))):"",Object.entries(t).map((l=>{var i,r,n=(0,C.A)(l,2),u=n[0],_=n[1];return a&&!_.main&&!_.showNarrow||_.hidden||(e.columnOrder&&e.columnOrder.includes(u)&&null!==(i=null===(r=e.hiddenColumns)||void 0===r?void 0:r.includes(u))&&void 0!==i?i:_.defaultHidden)?z.s6:(0,z.qy)(c||(c=Y`
            <div
              @mouseover=${0}
              @focus=${0}
              role=${0}
              class="mdc-data-table__cell ${0}"
              style=${0}
            >
              ${0}
            </div>
          `),e._setTitle,e._setTitle,_.main?"rowheader":"cell",(0,I.H)({"mdc-data-table__cell--flex":"flex"===_.type,"mdc-data-table__cell--numeric":"numeric"===_.type,"mdc-data-table__cell--icon":"icon"===_.type,"mdc-data-table__cell--icon-button":"icon-button"===_.type,"mdc-data-table__cell--overflow-menu":"overflow-menu"===_.type,"mdc-data-table__cell--overflow":"overflow"===_.type,forceLTR:Boolean(_.forceLTR)}),(0,q.W)({minWidth:_.minWidth,maxWidth:_.maxWidth,flex:_.flex||1}),_.template?_.template(o):a&&_.main?(0,z.qy)(d||(d=Y`<div class="primary">${0}</div>
                      <div class="secondary">
                        ${0}
                      </div>
                      ${0}`),o[u],Object.entries(t).filter((t=>{var a,o,l=(0,C.A)(t,2),i=l[0],r=l[1];return!(r.hidden||r.main||r.showNarrow||(e.columnOrder&&e.columnOrder.includes(i)&&null!==(a=null===(o=e.hiddenColumns)||void 0===o?void 0:o.includes(i))&&void 0!==a?a:r.defaultHidden))})).map(((e,t)=>{var a=(0,C.A)(e,2),l=a[0],i=a[1];return(0,z.qy)(s||(s=Y`${0}${0}`),0!==t?" · ":z.s6,i.template?i.template(o):o[l])})),_.extraTemplate?_.extraTemplate(o):z.s6):(0,z.qy)(h||(h=Y`${0}${0}`),o[u],_.extraTemplate?_.extraTemplate(o):z.s6))}))):z.s6,e._groupData=(0,T.A)(((t,a,o,l,i,r,n,c,d)=>{if(o||l||i){var s=(0,k.A)(t);if(i){var h=c===i,_=P(s,(e=>e[i]));_.undefined&&(_[Q]=_.undefined,delete _.undefined);var p=Object.keys(_).sort(((t,a)=>{var o,l;if(!r&&h){var i=(0,W.xL)(t,a,e.hass.locale.language);return"asc"===d?i:-1*i}var n=null!==(o=null==r?void 0:r.indexOf(t))&&void 0!==o?o:-1,c=null!==(l=null==r?void 0:r.indexOf(a))&&void 0!==l?l:-1;return n!==c?-1===n?1:-1===c?-1:n-c:(0,W.xL)(["","-","—"].includes(t)?"zzz":t,["","-","—"].includes(a)?"zzz":a,e.hass.locale.language)})).reduce(((e,t)=>{var a=[t,_[t]];return e.push(a),e}),[]),m=[];p.forEach((t=>{var o=(0,C.A)(t,2),l=o[0],i=o[1],r=n.includes(l);m.push({append:!0,selectable:!1,content:(0,z.qy)(u||(u=Y`<div
                class="mdc-data-table__cell group-header"
                role="cell"
                .group=${0}
                @click=${0}
              >
                <ha-icon-button
                  .path=${0}
                  .label=${0}
                  class=${0}
                >
                </ha-icon-button>
                ${0}
              </div>`),l,e._collapseGroup,"M7.41,15.41L12,10.83L16.59,15.41L18,14L12,8L6,14L7.41,15.41Z",e.hass.localize("ui.components.data-table."+(r?"expand":"collapse")),r?"collapsed":"",l===Q?a("ui.components.data-table.ungrouped"):l||"")}),n.includes(l)||m.push.apply(m,(0,k.A)(i))})),s=m}return o&&s.push({append:!0,selectable:!1,content:o}),l&&s.push({empty:!0}),s}return t})),e._memFilterData=(0,T.A)(((e,t,a)=>((e,t,a)=>N().filterData(e,t,a))(e,t,a))),e._handleRowCheckboxClicked=t=>{var a,o=t.currentTarget,l=o.rowId,i=e._groupData(e._filteredData,e.localizeFunc||e.hass.localize,e.appendRow,e.hasFab,e.groupColumn,e.groupOrder,e._collapsedGroups,e.sortColumn,e.sortDirection);if(!1!==(null===(a=i.find((t=>t[e.id]===l)))||void 0===a?void 0:a.selectable)){var r=i.findIndex((t=>t[e.id]===l));if(t instanceof MouseEvent&&t.shiftKey&&null!==e._lastSelectedRowId){var n=i.findIndex((t=>t[e.id]===e._lastSelectedRowId));n>-1&&r>-1&&(e._checkedRows=[].concat((0,k.A)(e._checkedRows),(0,k.A)(e._selectRange(i,n,r))))}else o.checked?e._checkedRows=e._checkedRows.filter((e=>e!==l)):e._checkedRows.includes(l)||(e._checkedRows=[].concat((0,k.A)(e._checkedRows),[l]));r>-1&&(e._lastSelectedRowId=l),e._checkedRowsChanged()}},e._handleRowClick=t=>{if(!t.composedPath().find((e=>["ha-checkbox","ha-button","ha-button","ha-icon-button","ha-assist-chip"].includes(e.localName)))){var a=t.currentTarget.rowId;(0,F.r)((0,$.A)(e),"row-click",{id:a},{bubbles:!1})}},e._collapseGroup=t=>{var a=t.currentTarget.group;e._collapsedGroups.includes(a)?e._collapsedGroups=e._collapsedGroups.filter((e=>e!==a)):e._collapsedGroups=[].concat((0,k.A)(e._collapsedGroups),[a]),e._lastSelectedRowId=null,(0,F.r)((0,$.A)(e),"collapsed-changed",{value:e._collapsedGroups})},e}return(0,M.A)(t,e),(0,A.A)(t,[{key:"clearSelection",value:function(){this._checkedRows=[],this._lastSelectedRowId=null,this._checkedRowsChanged()}},{key:"selectAll",value:function(){this._checkedRows=this._filteredData.filter((e=>!1!==e.selectable)).map((e=>e[this.id])),this._lastSelectedRowId=null,this._checkedRowsChanged()}},{key:"select",value:function(e,t){t&&(this._checkedRows=[]),e.forEach((e=>{var t=this._filteredData.find((t=>t[this.id]===e));!1===(null==t?void 0:t.selectable)||this._checkedRows.includes(e)||this._checkedRows.push(e)})),this._lastSelectedRowId=null,this._checkedRowsChanged()}},{key:"unselect",value:function(e){e.forEach((e=>{var t=this._checkedRows.indexOf(e);t>-1&&this._checkedRows.splice(t,1)})),this._lastSelectedRowId=null,this._checkedRowsChanged()}},{key:"connectedCallback",value:function(){(0,D.A)(t,"connectedCallback",this,3)([]),this._filteredData.length&&(this._filteredData=(0,k.A)(this._filteredData))}},{key:"firstUpdated",value:function(){this.updateComplete.then((()=>this._calcTableHeight()))}},{key:"updated",value:function(){var e=this.renderRoot.querySelector(".mdc-data-table__header-row");e&&(e.scrollWidth>e.clientWidth?this.style.setProperty("--table-row-width",`${e.scrollWidth}px`):this.style.removeProperty("--table-row-width"))}},{key:"willUpdate",value:function(e){if((0,D.A)(t,"willUpdate",this,3)([e]),this.hasUpdated||(0,j.i)(),e.has("columns")){if(this._filterable=Object.values(this.columns).some((e=>e.filterable)),!this.sortColumn)for(var a in this.columns)if(this.columns[a].direction){this.sortDirection=this.columns[a].direction,this.sortColumn=a,this._lastSelectedRowId=null,(0,F.r)(this,"sorting-changed",{column:a,direction:this.sortDirection});break}var o=(0,Z.A)(this.columns);Object.values(o).forEach((e=>{delete e.title,delete e.template,delete e.extraTemplate})),this._sortColumns=o}if(e.has("filter")&&(this._debounceSearch(this.filter),this._lastSelectedRowId=null),e.has("data")){if(this._checkedRows.length){var l=new Set(this.data.map((e=>String(e[this.id])))),i=this._checkedRows.filter((e=>l.has(e)));i.length!==this._checkedRows.length&&(this._checkedRows=i,this._checkedRowsChanged())}this._checkableRowsCount=this.data.filter((e=>!1!==e.selectable)).length}!this.hasUpdated&&this.initialCollapsedGroups?(this._collapsedGroups=this.initialCollapsedGroups,this._lastSelectedRowId=null,(0,F.r)(this,"collapsed-changed",{value:this._collapsedGroups})):e.has("groupColumn")&&(this._collapsedGroups=[],this._lastSelectedRowId=null,(0,F.r)(this,"collapsed-changed",{value:this._collapsedGroups})),(e.has("data")||e.has("columns")||e.has("_filter")||e.has("sortColumn")||e.has("sortDirection"))&&this._sortFilterData(),(e.has("_filter")||e.has("sortColumn")||e.has("sortDirection"))&&(this._lastSelectedRowId=null),(e.has("selectable")||e.has("hiddenColumns"))&&(this._filteredData=(0,k.A)(this._filteredData))}},{key:"render",value:function(){var e=this.localizeFunc||this.hass.localize,t=this._sortedColumns(this.columns,this.columnOrder);return(0,z.qy)(_||(_=Y`
      <div class="mdc-data-table">
        <slot name="header" @slotchange=${0}>
          ${0}
        </slot>
        <div
          class="mdc-data-table__table ${0}"
          role="table"
          aria-rowcount=${0}
          style=${0}
        >
          <div
            class="mdc-data-table__header-row"
            role="row"
            aria-rowindex="1"
            @scroll=${0}
          >
            <slot name="header-row">
              ${0}
              ${0}
            </slot>
          </div>
          ${0}
        </div>
      </div>
    `),this._calcTableHeight,this._filterable?(0,z.qy)(p||(p=Y`
                <div class="table-header">
                  <search-input
                    .hass=${0}
                    @value-changed=${0}
                    .label=${0}
                    .noLabelFloat=${0}
                  ></search-input>
                </div>
              `),this.hass,this._handleSearchChange,this.searchLabel,this.noLabelFloat):"",(0,I.H)({"auto-height":this.autoHeight}),this._filteredData.length+1,(0,q.W)({height:this.autoHeight?53*(this._filteredData.length||1)+53+"px":`calc(100% - ${this._headerHeight}px)`}),this._scrollContent,this.selectable?(0,z.qy)(m||(m=Y`
                    <div
                      class="mdc-data-table__header-cell mdc-data-table__header-cell--checkbox"
                      role="columnheader"
                    >
                      <ha-checkbox
                        class="mdc-data-table__row-checkbox"
                        @change=${0}
                        .indeterminate=${0}
                        .checked=${0}
                      >
                      </ha-checkbox>
                    </div>
                  `),this._handleHeaderRowCheckboxClick,this._checkedRows.length&&this._checkedRows.length!==this._checkableRowsCount,this._checkedRows.length&&this._checkedRows.length===this._checkableRowsCount):"",Object.entries(t).map((e=>{var t,a,o=(0,C.A)(e,2),l=o[0],i=o[1];if(i.hidden||(this.columnOrder&&this.columnOrder.includes(l)&&null!==(t=null===(a=this.hiddenColumns)||void 0===a?void 0:a.includes(l))&&void 0!==t?t:i.defaultHidden))return z.s6;var r=l===this.sortColumn,n={"mdc-data-table__header-cell--numeric":"numeric"===i.type,"mdc-data-table__header-cell--icon":"icon"===i.type,"mdc-data-table__header-cell--icon-button":"icon-button"===i.type,"mdc-data-table__header-cell--overflow-menu":"overflow-menu"===i.type,"mdc-data-table__header-cell--overflow":"overflow"===i.type,sortable:Boolean(i.sortable),"not-sorted":Boolean(i.sortable&&!r)};return(0,z.qy)(b||(b=Y`
                  <div
                    aria-label=${0}
                    class="mdc-data-table__header-cell ${0}"
                    style=${0}
                    role="columnheader"
                    aria-sort=${0}
                    @click=${0}
                    .columnId=${0}
                    title=${0}
                  >
                    ${0}
                    <span>${0}</span>
                  </div>
                `),(0,O.J)(i.label),(0,I.H)(n),(0,q.W)({minWidth:i.minWidth,maxWidth:i.maxWidth,flex:i.flex||1}),(0,O.J)(r?"desc"===this.sortDirection?"descending":"ascending":void 0),this._handleHeaderClick,l,(0,O.J)(i.title),i.sortable?(0,z.qy)(f||(f=Y`
                          <ha-svg-icon
                            .path=${0}
                          ></ha-svg-icon>
                        `),r&&"desc"===this.sortDirection?"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z":"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z"):"",i.title)})),this._filteredData.length?(0,z.qy)(g||(g=Y`
                <lit-virtualizer
                  scroller
                  class="mdc-data-table__content scroller ha-scrollbar"
                  @scroll=${0}
                  .items=${0}
                  .keyFunction=${0}
                  .renderItem=${0}
                ></lit-virtualizer>
              `),this._saveScrollPos,this._groupData(this._filteredData,e,this.appendRow,this.hasFab,this.groupColumn,this.groupOrder,this._collapsedGroups,this.sortColumn,this.sortDirection),this._keyFunction,((e,a)=>this._renderRow(t,this.narrow,e,a))):(0,z.qy)(v||(v=Y`
                <div class="mdc-data-table__content">
                  <div class="mdc-data-table__row" role="row">
                    <div class="mdc-data-table__cell grows center" role="cell">
                      ${0}
                    </div>
                  </div>
                </div>
              `),this.noDataText||e("ui.components.data-table.no-data")))}},{key:"_sortFilterData",value:(o=(0,x.A)((0,w.A)().m((function e(){var t,a,o,l,i,r,n,c,d,s,h;return(0,w.A)().w((function(e){for(;;)switch(e.n){case 0:if(t=(new Date).getTime(),a=t-this._lastUpdate,o=t-this._curRequest,this._curRequest=t,l=!this._lastUpdate||a>500&&o<500,i=this.data,!this._filter){e.n=2;break}return e.n=1,this._memFilterData(this.data,this._sortColumns,this._filter.trim());case 1:i=e.v;case 2:if(l||this._curRequest===t){e.n=3;break}return e.a(2);case 3:return r=this.sortColumn&&this._sortColumns[this.sortColumn]?J(i,this._sortColumns[this.sortColumn],this.sortDirection,this.sortColumn,this.hass.locale.language):i,e.n=4,Promise.all([r,K.E]);case 4:if(n=e.v,c=(0,C.A)(n,1),d=c[0],s=(new Date).getTime(),!((h=s-t)<100)){e.n=5;break}return e.n=5,new Promise((e=>{setTimeout(e,100-h)}));case 5:if(l||this._curRequest===t){e.n=6;break}return e.a(2);case 6:this._lastUpdate=t,this._filteredData=d;case 7:return e.a(2)}}),e,this)}))),function(){return o.apply(this,arguments)})},{key:"_handleHeaderClick",value:function(e){var t=e.currentTarget.columnId;this.columns[t].sortable&&(this.sortDirection&&this.sortColumn===t?"asc"===this.sortDirection?this.sortDirection="desc":this.sortDirection=null:this.sortDirection="asc",this.sortColumn=null===this.sortDirection?void 0:t,(0,F.r)(this,"sorting-changed",{column:t,direction:this.sortDirection}))}},{key:"_handleHeaderRowCheckboxClick",value:function(e){e.target.checked?this.selectAll():(this._checkedRows=[],this._checkedRowsChanged()),this._lastSelectedRowId=null}},{key:"_selectRange",value:function(e,t,a){for(var o=Math.min(t,a),l=Math.max(t,a),i=[],r=o;r<=l;r++){var n=e[r];n&&!1!==n.selectable&&!this._checkedRows.includes(n[this.id])&&i.push(n[this.id])}return i}},{key:"_setTitle",value:function(e){var t=e.currentTarget;t.scrollWidth>t.offsetWidth&&t.setAttribute("title",t.innerText)}},{key:"_checkedRowsChanged",value:function(){this._filteredData.length&&(this._filteredData=(0,k.A)(this._filteredData)),(0,F.r)(this,"selection-changed",{value:this._checkedRows})}},{key:"_handleSearchChange",value:function(e){this.filter||(this._lastSelectedRowId=null,this._debounceSearch(e.detail.value))}},{key:"_calcTableHeight",value:(a=(0,x.A)((0,w.A)().m((function e(){return(0,w.A)().w((function(e){for(;;)switch(e.n){case 0:if(!this.autoHeight){e.n=1;break}return e.a(2);case 1:return e.n=2,this.updateComplete;case 2:this._headerHeight=this._header.clientHeight;case 3:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"_saveScrollPos",value:function(e){this._savedScrollPos=e.target.scrollTop,this.renderRoot.querySelector(".mdc-data-table__header-row").scrollLeft=e.target.scrollLeft}},{key:"_scrollContent",value:function(e){this.renderRoot.querySelector("lit-virtualizer").scrollLeft=e.target.scrollLeft}},{key:"expandAllGroups",value:function(){this._collapsedGroups=[],this._lastSelectedRowId=null,(0,F.r)(this,"collapsed-changed",{value:this._collapsedGroups})}},{key:"collapseAllGroups",value:function(){if(this.groupColumn&&this.data.some((e=>e[this.groupColumn]))){var e=P(this.data,(e=>e[this.groupColumn]));e.undefined&&(e[Q]=e.undefined,delete e.undefined),this._collapsedGroups=Object.keys(e),this._lastSelectedRowId=null,(0,F.r)(this,"collapsed-changed",{value:this._collapsedGroups})}}}],[{key:"styles",get:function(){return[U.dp,(0,z.AH)(y||(y=Y`
        /* default mdc styles, colors changed, without checkbox styles */
        :host {
          height: 100%;
        }
        .mdc-data-table__content {
          font-family: var(--ha-font-family-body);
          -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
          -webkit-font-smoothing: var(--ha-font-smoothing);
          font-size: 0.875rem;
          line-height: var(--ha-line-height-condensed);
          font-weight: var(--ha-font-weight-normal);
          letter-spacing: 0.0178571429em;
          text-decoration: inherit;
          text-transform: inherit;
        }

        .mdc-data-table {
          background-color: var(--data-table-background-color);
          border-radius: var(--ha-border-radius-sm);
          border-width: 1px;
          border-style: solid;
          border-color: var(--divider-color);
          display: inline-flex;
          flex-direction: column;
          box-sizing: border-box;
          overflow: hidden;
        }

        .mdc-data-table__row--selected {
          background-color: rgba(var(--rgb-primary-color), 0.04);
        }

        .mdc-data-table__row {
          display: flex;
          height: var(--data-table-row-height, 52px);
          width: var(--table-row-width, 100%);
        }

        .mdc-data-table__row.empty-row {
          height: var(
            --data-table-empty-row-height,
            var(--data-table-row-height, 52px)
          );
        }

        .mdc-data-table__row ~ .mdc-data-table__row {
          border-top: 1px solid var(--divider-color);
        }

        .mdc-data-table__row.clickable:not(
            .mdc-data-table__row--selected
          ):hover {
          background-color: rgba(var(--rgb-primary-text-color), 0.04);
        }

        .mdc-data-table__header-cell {
          color: var(--primary-text-color);
        }

        .mdc-data-table__cell {
          color: var(--primary-text-color);
        }

        .mdc-data-table__header-row {
          height: 56px;
          display: flex;
          border-bottom: 1px solid var(--divider-color);
          overflow: auto;
        }

        /* Hide scrollbar for Chrome, Safari and Opera */
        .mdc-data-table__header-row::-webkit-scrollbar {
          display: none;
        }

        /* Hide scrollbar for IE, Edge and Firefox */
        .mdc-data-table__header-row {
          -ms-overflow-style: none; /* IE and Edge */
          scrollbar-width: none; /* Firefox */
        }

        .mdc-data-table__cell,
        .mdc-data-table__header-cell {
          padding-right: 16px;
          padding-left: 16px;
          min-width: 150px;
          align-self: center;
          overflow: hidden;
          text-overflow: ellipsis;
          flex-shrink: 0;
          box-sizing: border-box;
        }

        .mdc-data-table__cell.mdc-data-table__cell--flex {
          display: flex;
          overflow: initial;
        }

        .mdc-data-table__cell.mdc-data-table__cell--icon {
          overflow: initial;
        }

        .mdc-data-table__header-cell--checkbox,
        .mdc-data-table__cell--checkbox {
          /* @noflip */
          padding-left: 16px;
          /* @noflip */
          padding-right: 0;
          /* @noflip */
          padding-inline-start: 16px;
          /* @noflip */
          padding-inline-end: initial;
          width: 60px;
          min-width: 60px;
        }

        .mdc-data-table__table {
          height: 100%;
          width: 100%;
          border: 0;
          white-space: nowrap;
          position: relative;
        }

        .mdc-data-table__cell {
          font-family: var(--ha-font-family-body);
          -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
          -webkit-font-smoothing: var(--ha-font-smoothing);
          font-size: 0.875rem;
          line-height: var(--ha-line-height-condensed);
          font-weight: var(--ha-font-weight-normal);
          letter-spacing: 0.0178571429em;
          text-decoration: inherit;
          text-transform: inherit;
          flex-grow: 0;
          flex-shrink: 0;
        }

        .mdc-data-table__cell a {
          color: inherit;
          text-decoration: none;
        }

        .mdc-data-table__cell--numeric {
          text-align: var(--float-end);
        }

        .mdc-data-table__cell--icon {
          color: var(--secondary-text-color);
          text-align: center;
        }

        .mdc-data-table__header-cell--icon,
        .mdc-data-table__cell--icon {
          min-width: 64px;
          flex: 0 0 64px !important;
        }

        .mdc-data-table__cell--icon img {
          width: 24px;
          height: 24px;
        }

        .mdc-data-table__header-cell.mdc-data-table__header-cell--icon {
          text-align: center;
        }

        .mdc-data-table__header-cell.sortable.mdc-data-table__header-cell--icon:hover,
        .mdc-data-table__header-cell.sortable.mdc-data-table__header-cell--icon:not(
            .not-sorted
          ) {
          text-align: var(--float-start);
        }

        .mdc-data-table__cell--icon:first-child img,
        .mdc-data-table__cell--icon:first-child ha-icon,
        .mdc-data-table__cell--icon:first-child ha-svg-icon,
        .mdc-data-table__cell--icon:first-child ha-state-icon,
        .mdc-data-table__cell--icon:first-child ha-domain-icon,
        .mdc-data-table__cell--icon:first-child ha-service-icon {
          margin-left: 8px;
          margin-inline-start: 8px;
          margin-inline-end: initial;
        }

        .mdc-data-table__cell--icon:first-child state-badge {
          margin-right: -8px;
          margin-inline-end: -8px;
          margin-inline-start: initial;
        }

        .mdc-data-table__cell--overflow-menu,
        .mdc-data-table__header-cell--overflow-menu,
        .mdc-data-table__header-cell--icon-button,
        .mdc-data-table__cell--icon-button {
          min-width: 64px;
          flex: 0 0 64px !important;
          padding: 8px;
        }

        .mdc-data-table__header-cell--icon-button,
        .mdc-data-table__cell--icon-button {
          min-width: 56px;
          width: 56px;
        }

        .mdc-data-table__cell--overflow-menu,
        .mdc-data-table__cell--icon-button {
          color: var(--secondary-text-color);
          text-overflow: clip;
        }

        .mdc-data-table__header-cell--icon-button:first-child,
        .mdc-data-table__cell--icon-button:first-child,
        .mdc-data-table__header-cell--icon-button:last-child,
        .mdc-data-table__cell--icon-button:last-child {
          width: 64px;
        }

        .mdc-data-table__cell--overflow-menu:first-child,
        .mdc-data-table__header-cell--overflow-menu:first-child,
        .mdc-data-table__header-cell--icon-button:first-child,
        .mdc-data-table__cell--icon-button:first-child {
          padding-left: 16px;
          padding-inline-start: 16px;
          padding-inline-end: initial;
        }

        .mdc-data-table__cell--overflow-menu:last-child,
        .mdc-data-table__header-cell--overflow-menu:last-child,
        .mdc-data-table__header-cell--icon-button:last-child,
        .mdc-data-table__cell--icon-button:last-child {
          padding-right: 16px;
          padding-inline-end: 16px;
          padding-inline-start: initial;
        }
        .mdc-data-table__cell--overflow-menu,
        .mdc-data-table__cell--overflow,
        .mdc-data-table__header-cell--overflow-menu,
        .mdc-data-table__header-cell--overflow {
          overflow: initial;
        }
        .mdc-data-table__cell--icon-button a {
          color: var(--secondary-text-color);
        }

        .mdc-data-table__header-cell {
          font-family: var(--ha-font-family-body);
          -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
          -webkit-font-smoothing: var(--ha-font-smoothing);
          font-size: var(--ha-font-size-s);
          line-height: var(--ha-line-height-normal);
          font-weight: var(--ha-font-weight-medium);
          letter-spacing: 0.0071428571em;
          text-decoration: inherit;
          text-transform: inherit;
          text-align: var(--float-start);
        }

        .mdc-data-table__header-cell--numeric {
          text-align: var(--float-end);
        }
        .mdc-data-table__header-cell--numeric.sortable:hover,
        .mdc-data-table__header-cell--numeric.sortable:not(.not-sorted) {
          text-align: var(--float-start);
        }

        /* custom from here */

        .group-header {
          padding-top: 12px;
          height: var(--data-table-row-height, 52px);
          padding-left: 12px;
          padding-inline-start: 12px;
          padding-inline-end: initial;
          width: 100%;
          font-weight: var(--ha-font-weight-medium);
          display: flex;
          align-items: center;
          cursor: pointer;
          background-color: var(--primary-background-color);
        }

        .group-header ha-icon-button {
          transition: transform 0.2s ease;
        }

        .group-header ha-icon-button.collapsed {
          transform: rotate(180deg);
        }

        :host {
          display: block;
        }

        .mdc-data-table {
          display: block;
          border-width: var(--data-table-border-width, 1px);
          height: 100%;
        }
        .mdc-data-table__header-cell {
          overflow: hidden;
          position: relative;
        }
        .mdc-data-table__header-cell span {
          position: relative;
          left: 0px;
          inset-inline-start: 0px;
          inset-inline-end: initial;
        }

        .mdc-data-table__header-cell.sortable {
          cursor: pointer;
        }
        .mdc-data-table__header-cell > * {
          transition: var(--float-start) 0.2s ease;
        }
        .mdc-data-table__header-cell ha-svg-icon {
          top: -3px;
          position: absolute;
        }
        .mdc-data-table__header-cell.not-sorted ha-svg-icon {
          left: -20px;
          inset-inline-start: -20px;
          inset-inline-end: initial;
        }
        .mdc-data-table__header-cell.sortable:not(.not-sorted) span,
        .mdc-data-table__header-cell.sortable.not-sorted:hover span {
          left: 24px;
          inset-inline-start: 24px;
          inset-inline-end: initial;
        }
        .mdc-data-table__header-cell.sortable:not(.not-sorted) ha-svg-icon,
        .mdc-data-table__header-cell.sortable:hover.not-sorted ha-svg-icon {
          left: 12px;
          inset-inline-start: 12px;
          inset-inline-end: initial;
        }
        .table-header {
          border-bottom: 1px solid var(--divider-color);
        }
        search-input {
          display: block;
          flex: 1;
          --mdc-text-field-fill-color: var(--sidebar-background-color);
          --mdc-text-field-idle-line-color: transparent;
        }
        slot[name="header"] {
          display: block;
        }
        .center {
          text-align: center;
        }
        .secondary {
          color: var(--secondary-text-color);
        }
        .scroller {
          height: calc(100% - 57px);
          overflow: overlay !important;
        }

        .mdc-data-table__table.auto-height .scroller {
          overflow-y: hidden !important;
        }
        .grows {
          flex-grow: 1;
          flex-shrink: 1;
        }
        .forceLTR {
          direction: ltr;
        }
        .clickable {
          cursor: pointer;
        }
        lit-virtualizer {
          contain: size layout !important;
          overscroll-behavior: contain;
        }
      `))]}}]);var a,o}(z.WF);(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"hass",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"localizeFunc",void 0),(0,S.__decorate)([(0,H.MZ)({type:Boolean})],X.prototype,"narrow",void 0),(0,S.__decorate)([(0,H.MZ)({type:Object})],X.prototype,"columns",void 0),(0,S.__decorate)([(0,H.MZ)({type:Array})],X.prototype,"data",void 0),(0,S.__decorate)([(0,H.MZ)({type:Boolean})],X.prototype,"selectable",void 0),(0,S.__decorate)([(0,H.MZ)({type:Boolean})],X.prototype,"clickable",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:"has-fab",type:Boolean})],X.prototype,"hasFab",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"appendRow",void 0),(0,S.__decorate)([(0,H.MZ)({type:Boolean,attribute:"auto-height"})],X.prototype,"autoHeight",void 0),(0,S.__decorate)([(0,H.MZ)({type:String})],X.prototype,"id",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1,type:String})],X.prototype,"noDataText",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1,type:String})],X.prototype,"searchLabel",void 0),(0,S.__decorate)([(0,H.MZ)({type:Boolean,attribute:"no-label-float"})],X.prototype,"noLabelFloat",void 0),(0,S.__decorate)([(0,H.MZ)({type:String})],X.prototype,"filter",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"groupColumn",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"groupOrder",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"sortColumn",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"sortDirection",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"initialCollapsedGroups",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"hiddenColumns",void 0),(0,S.__decorate)([(0,H.MZ)({attribute:!1})],X.prototype,"columnOrder",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_filterable",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_filter",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_filteredData",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_headerHeight",void 0),(0,S.__decorate)([(0,H.P)("slot[name='header']")],X.prototype,"_header",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_collapsedGroups",void 0),(0,S.__decorate)([(0,H.wk)()],X.prototype,"_lastSelectedRowId",void 0),(0,S.__decorate)([(0,G.a)(".scroller")],X.prototype,"_savedScrollPos",void 0),(0,S.__decorate)([(0,H.Ls)({passive:!0})],X.prototype,"_saveScrollPos",null),(0,S.__decorate)([(0,H.Ls)({passive:!0})],X.prototype,"_scrollContent",null),X=(0,S.__decorate)([(0,H.EM)("ha-data-table")],X)},63419:function(e,t,a){var o,l=a(44734),i=a(56038),r=a(69683),n=a(6454),c=(a(28706),a(62826)),d=a(96196),s=a(77845),h=a(92542),u=(a(41742),a(25460)),_=a(26139),p=a(8889),m=a(63374),b=function(e){function t(){return(0,l.A)(this,t),(0,r.A)(this,t,arguments)}return(0,n.A)(t,e),(0,i.A)(t,[{key:"connectedCallback",value:function(){(0,u.A)(t,"connectedCallback",this,3)([]),this.addEventListener("close-menu",this._handleCloseMenu)}},{key:"_handleCloseMenu",value:function(e){var t,a;e.detail.reason.kind===m.fi.KEYDOWN&&e.detail.reason.key===m.NV.ESCAPE||null===(t=(a=e.detail.initiator).clickAction)||void 0===t||t.call(a,e.detail.initiator)}}])}(_.W1);b.styles=[p.R,(0,d.AH)(o||(o=(e=>e)`
      :host {
        --md-sys-color-surface-container: var(--card-background-color);
      }
    `))],b=(0,c.__decorate)([(0,s.EM)("ha-md-menu")],b);var f,v,g=e=>e,y=function(e){function t(){var e;(0,l.A)(this,t);for(var a=arguments.length,o=new Array(a),i=0;i<a;i++)o[i]=arguments[i];return(e=(0,r.A)(this,t,[].concat(o))).disabled=!1,e.anchorCorner="end-start",e.menuCorner="start-start",e.hasOverflow=!1,e.quick=!1,e}return(0,n.A)(t,e),(0,i.A)(t,[{key:"items",get:function(){return this._menu.items}},{key:"focus",value:function(){var e;this._menu.open?this._menu.focus():null===(e=this._triggerButton)||void 0===e||e.focus()}},{key:"render",value:function(){return(0,d.qy)(f||(f=g`
      <div @click=${0}>
        <slot name="trigger" @slotchange=${0}></slot>
      </div>
      <ha-md-menu
        .quick=${0}
        .positioning=${0}
        .hasOverflow=${0}
        .anchorCorner=${0}
        .menuCorner=${0}
        @opening=${0}
        @closing=${0}
      >
        <slot></slot>
      </ha-md-menu>
    `),this._handleClick,this._setTriggerAria,this.quick,this.positioning,this.hasOverflow,this.anchorCorner,this.menuCorner,this._handleOpening,this._handleClosing)}},{key:"_handleOpening",value:function(){(0,h.r)(this,"opening",void 0,{composed:!1})}},{key:"_handleClosing",value:function(){(0,h.r)(this,"closing",void 0,{composed:!1})}},{key:"_handleClick",value:function(){this.disabled||(this._menu.anchorElement=this,this._menu.open?this._menu.close():this._menu.show())}},{key:"_triggerButton",get:function(){return this.querySelector('ha-icon-button[slot="trigger"], ha-button[slot="trigger"], ha-assist-chip[slot="trigger"]')}},{key:"_setTriggerAria",value:function(){this._triggerButton&&(this._triggerButton.ariaHasPopup="menu")}}])}(d.WF);y.styles=(0,d.AH)(v||(v=g`
    :host {
      display: inline-block;
      position: relative;
    }
    ::slotted([disabled]) {
      color: var(--disabled-text-color);
    }
  `)),(0,c.__decorate)([(0,s.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,c.__decorate)([(0,s.MZ)()],y.prototype,"positioning",void 0),(0,c.__decorate)([(0,s.MZ)({attribute:"anchor-corner"})],y.prototype,"anchorCorner",void 0),(0,c.__decorate)([(0,s.MZ)({attribute:"menu-corner"})],y.prototype,"menuCorner",void 0),(0,c.__decorate)([(0,s.MZ)({type:Boolean,attribute:"has-overflow"})],y.prototype,"hasOverflow",void 0),(0,c.__decorate)([(0,s.MZ)({type:Boolean})],y.prototype,"quick",void 0),(0,c.__decorate)([(0,s.P)("ha-md-menu",!0)],y.prototype,"_menu",void 0),y=(0,c.__decorate)([(0,s.EM)("ha-md-button-menu")],y)},32072:function(e,t,a){var o,l=a(56038),i=a(44734),r=a(69683),n=a(6454),c=a(62826),d=a(10414),s=a(18989),h=a(96196),u=a(77845),_=function(e){function t(){return(0,i.A)(this,t),(0,r.A)(this,t,arguments)}return(0,n.A)(t,e),(0,l.A)(t)}(d.c);_.styles=[s.R,(0,h.AH)(o||(o=(e=>e)`
      :host {
        --md-divider-color: var(--divider-color);
      }
    `))],_=(0,c.__decorate)([(0,u.EM)("ha-md-divider")],_)},99892:function(e,t,a){var o,l=a(56038),i=a(44734),r=a(69683),n=a(6454),c=a(62826),d=a(54407),s=a(28522),h=a(96196),u=a(77845),_=function(e){function t(){return(0,i.A)(this,t),(0,r.A)(this,t,arguments)}return(0,n.A)(t,e),(0,l.A)(t)}(d.K);_.styles=[s.R,(0,h.AH)(o||(o=(e=>e)`
      :host {
        --ha-icon-display: block;
        --md-sys-color-primary: var(--primary-text-color);
        --md-sys-color-on-primary: var(--primary-text-color);
        --md-sys-color-secondary: var(--secondary-text-color);
        --md-sys-color-surface: var(--card-background-color);
        --md-sys-color-on-surface: var(--primary-text-color);
        --md-sys-color-on-surface-variant: var(--secondary-text-color);
        --md-sys-color-secondary-container: rgba(
          var(--rgb-primary-color),
          0.15
        );
        --md-sys-color-on-secondary-container: var(--text-primary-color);
        --mdc-icon-size: 16px;

        --md-sys-color-on-primary-container: var(--primary-text-color);
        --md-sys-color-on-secondary-container: var(--primary-text-color);
        --md-menu-item-label-text-font: Roboto, sans-serif;
      }
      :host(.warning) {
        --md-menu-item-label-text-color: var(--error-color);
        --md-menu-item-leading-icon-color: var(--error-color);
      }
      ::slotted([slot="headline"]) {
        text-wrap: nowrap;
      }
      :host([disabled]) {
        opacity: 1;
        --md-menu-item-label-text-color: var(--disabled-text-color);
        --md-menu-item-leading-icon-color: var(--disabled-text-color);
      }
    `))],(0,c.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"clickAction",void 0),_=(0,c.__decorate)([(0,u.EM)("ha-md-menu-item")],_)},17262:function(e,t,a){var o,l,i,r=a(61397),n=a(50264),c=a(44734),d=a(56038),s=a(69683),h=a(6454),u=(a(28706),a(2008),a(18111),a(22489),a(26099),a(62826)),_=a(96196),p=a(77845),m=(a(60733),a(60961),a(78740),a(92542)),b=e=>e,f=function(e){function t(){var e;(0,c.A)(this,t);for(var a=arguments.length,o=new Array(a),l=0;l<a;l++)o[l]=arguments[l];return(e=(0,s.A)(this,t,[].concat(o))).suffix=!1,e.autofocus=!1,e}return(0,h.A)(t,e),(0,d.A)(t,[{key:"focus",value:function(){var e;null===(e=this._input)||void 0===e||e.focus()}},{key:"render",value:function(){return(0,_.qy)(o||(o=b`
      <ha-textfield
        .autofocus=${0}
        autocomplete="off"
        .label=${0}
        .value=${0}
        icon
        .iconTrailing=${0}
        @input=${0}
      >
        <slot name="prefix" slot="leadingIcon">
          <ha-svg-icon
            tabindex="-1"
            class="prefix"
            .path=${0}
          ></ha-svg-icon>
        </slot>
        <div class="trailing" slot="trailingIcon">
          ${0}
          <slot name="suffix"></slot>
        </div>
      </ha-textfield>
    `),this.autofocus,this.label||this.hass.localize("ui.common.search"),this.filter||"",this.filter||this.suffix,this._filterInputChanged,"M9.5,3A6.5,6.5 0 0,1 16,9.5C16,11.11 15.41,12.59 14.44,13.73L14.71,14H15.5L20.5,19L19,20.5L14,15.5V14.71L13.73,14.44C12.59,15.41 11.11,16 9.5,16A6.5,6.5 0 0,1 3,9.5A6.5,6.5 0 0,1 9.5,3M9.5,5C7,5 5,7 5,9.5C5,12 7,14 9.5,14C12,14 14,12 14,9.5C14,7 12,5 9.5,5Z",this.filter&&(0,_.qy)(l||(l=b`
            <ha-icon-button
              @click=${0}
              .label=${0}
              .path=${0}
              class="clear-button"
            ></ha-icon-button>
          `),this._clearSearch,this.hass.localize("ui.common.clear"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"))}},{key:"_filterChanged",value:(u=(0,n.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:(0,m.r)(this,"value-changed",{value:String(t)});case 1:return e.a(2)}}),e,this)}))),function(e){return u.apply(this,arguments)})},{key:"_filterInputChanged",value:(i=(0,n.A)((0,r.A)().m((function e(t){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:this._filterChanged(t.target.value);case 1:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_clearSearch",value:(a=(0,n.A)((0,r.A)().m((function e(){return(0,r.A)().w((function(e){for(;;)switch(e.n){case 0:this._filterChanged("");case 1:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})}]);var a,i,u}(_.WF);f.styles=(0,_.AH)(i||(i=b`
    :host {
      display: inline-flex;
    }
    ha-svg-icon,
    ha-icon-button {
      color: var(--primary-text-color);
    }
    ha-svg-icon {
      outline: none;
    }
    .clear-button {
      --mdc-icon-size: 20px;
    }
    ha-textfield {
      display: inherit;
    }
    .trailing {
      display: flex;
      align-items: center;
    }
  `)),(0,u.__decorate)([(0,p.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,u.__decorate)([(0,p.MZ)()],f.prototype,"filter",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean})],f.prototype,"suffix",void 0),(0,u.__decorate)([(0,p.MZ)({type:Boolean})],f.prototype,"autofocus",void 0),(0,u.__decorate)([(0,p.MZ)({type:String})],f.prototype,"label",void 0),(0,u.__decorate)([(0,p.P)("ha-textfield",!0)],f.prototype,"_input",void 0),f=(0,u.__decorate)([(0,p.EM)("search-input")],f)}}]);
//# sourceMappingURL=4894.edf2f007888c841d.js.map