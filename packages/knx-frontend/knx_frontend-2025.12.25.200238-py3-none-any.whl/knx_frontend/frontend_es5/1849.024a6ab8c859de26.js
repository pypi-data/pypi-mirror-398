"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1849"],{59006:function(e,t,a){a.d(t,{J:function(){return r}});a(74423);var i=a(22786),o=a(81793),r=(0,i.A)((e=>{if(e.time_format===o.Hg.language||e.time_format===o.Hg.system){var t=e.time_format===o.Hg.language?e.language:void 0;return new Date("January 1, 2023 22:00:00").toLocaleString(t).includes("10")}return e.time_format===o.Hg.am_pm}))},29261:function(e,t,a){var i,o,r,l,d,n,s,h,u,c=a(44734),p=a(56038),m=a(69683),b=a(6454),v=(a(28706),a(2892),a(26099),a(38781),a(68156),a(62826)),y=a(96196),f=a(77845),_=a(32288),g=a(92542),x=a(55124),$=(a(60733),a(56768),a(56565),a(69869),a(78740),e=>e),M=function(e){function t(){var e;(0,c.A)(this,t);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(e=(0,m.A)(this,t,[].concat(i))).autoValidate=!1,e.required=!1,e.format=12,e.disabled=!1,e.days=0,e.hours=0,e.minutes=0,e.seconds=0,e.milliseconds=0,e.dayLabel="",e.hourLabel="",e.minLabel="",e.secLabel="",e.millisecLabel="",e.enableSecond=!1,e.enableMillisecond=!1,e.enableDay=!1,e.noHoursLimit=!1,e.amPm="AM",e}return(0,b.A)(t,e),(0,p.A)(t,[{key:"render",value:function(){return(0,y.qy)(i||(i=$`
      ${0}
      <div class="time-input-wrap-wrap">
        <div class="time-input-wrap">
          ${0}

          <ha-textfield
            id="hour"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            name="hours"
            @change=${0}
            @focusin=${0}
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max=${0}
            min="0"
            .disabled=${0}
            suffix=":"
            class="hasSuffix"
          >
          </ha-textfield>
          <ha-textfield
            id="min"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            @change=${0}
            @focusin=${0}
            name="minutes"
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max="59"
            min="0"
            .disabled=${0}
            .suffix=${0}
            class=${0}
          >
          </ha-textfield>
          ${0}
          ${0}
          ${0}
        </div>

        ${0}
      </div>
      ${0}
    `),this.label?(0,y.qy)(o||(o=$`<label>${0}${0}</label>`),this.label,this.required?" *":""):y.s6,this.enableDay?(0,y.qy)(r||(r=$`
                <ha-textfield
                  id="day"
                  type="number"
                  inputmode="numeric"
                  .value=${0}
                  .label=${0}
                  name="days"
                  @change=${0}
                  @focusin=${0}
                  no-spinner
                  .required=${0}
                  .autoValidate=${0}
                  min="0"
                  .disabled=${0}
                  suffix=":"
                  class="hasSuffix"
                >
                </ha-textfield>
              `),this.days.toFixed(),this.dayLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):y.s6,this.hours.toFixed(),this.hourLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,(0,_.J)(this._hourMax),this.disabled,this._formatValue(this.minutes),this.minLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableSecond?":":"",this.enableSecond?"has-suffix":"",this.enableSecond?(0,y.qy)(l||(l=$`<ha-textfield
                id="sec"
                type="number"
                inputmode="numeric"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="seconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="2"
                max="59"
                min="0"
                .disabled=${0}
                .suffix=${0}
                class=${0}
              >
              </ha-textfield>`),this._formatValue(this.seconds),this.secLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableMillisecond?":":"",this.enableMillisecond?"has-suffix":""):y.s6,this.enableMillisecond?(0,y.qy)(d||(d=$`<ha-textfield
                id="millisec"
                type="number"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="milliseconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="3"
                max="999"
                min="0"
                .disabled=${0}
              >
              </ha-textfield>`),this._formatValue(this.milliseconds,3),this.millisecLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):y.s6,!this.clearable||this.required||this.disabled?y.s6:(0,y.qy)(n||(n=$`<ha-icon-button
                label="clear"
                @click=${0}
                .path=${0}
              ></ha-icon-button>`),this._clearValue,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"),24===this.format?y.s6:(0,y.qy)(s||(s=$`<ha-select
              .required=${0}
              .value=${0}
              .disabled=${0}
              name="amPm"
              naturalMenuWidth
              fixedMenuPosition
              @selected=${0}
              @closed=${0}
            >
              <ha-list-item value="AM">AM</ha-list-item>
              <ha-list-item value="PM">PM</ha-list-item>
            </ha-select>`),this.required,this.amPm,this.disabled,this._valueChanged,x.d),this.helper?(0,y.qy)(h||(h=$`<ha-input-helper-text .disabled=${0}
            >${0}</ha-input-helper-text
          >`),this.disabled,this.helper):y.s6)}},{key:"_clearValue",value:function(){(0,g.r)(this,"value-changed")}},{key:"_valueChanged",value:function(e){var t=e.currentTarget;this[t.name]="amPm"===t.name?t.value:Number(t.value);var a={hours:this.hours,minutes:this.minutes,seconds:this.seconds,milliseconds:this.milliseconds};this.enableDay&&(a.days=this.days),12===this.format&&(a.amPm=this.amPm),(0,g.r)(this,"value-changed",{value:a})}},{key:"_onFocus",value:function(e){e.currentTarget.select()}},{key:"_formatValue",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;return e.toString().padStart(t,"0")}},{key:"_hourMax",get:function(){if(!this.noHoursLimit)return 12===this.format?12:23}}])}(y.WF);M.styles=(0,y.AH)(u||(u=$`
    :host([clearable]) {
      position: relative;
    }
    .time-input-wrap-wrap {
      display: flex;
    }
    .time-input-wrap {
      display: flex;
      flex: var(--time-input-flex, unset);
      border-radius: var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--ha-border-radius-square) var(--ha-border-radius-square);
      overflow: hidden;
      position: relative;
      direction: ltr;
      padding-right: 3px;
    }
    ha-textfield {
      width: 60px;
      flex-grow: 1;
      text-align: center;
      --mdc-shape-small: 0;
      --text-field-appearance: none;
      --text-field-padding: 0 4px;
      --text-field-suffix-padding-left: 2px;
      --text-field-suffix-padding-right: 0;
      --text-field-text-align: center;
    }
    ha-textfield.hasSuffix {
      --text-field-padding: 0 0 0 4px;
    }
    ha-textfield:first-child {
      --text-field-border-top-left-radius: var(--mdc-shape-medium);
    }
    ha-textfield:last-child {
      --text-field-border-top-right-radius: var(--mdc-shape-medium);
    }
    ha-select {
      --mdc-shape-small: 0;
      width: 85px;
    }
    :host([clearable]) .mdc-select__anchor {
      padding-inline-end: var(--select-selected-text-padding-end, 12px);
    }
    ha-icon-button {
      position: relative;
      --mdc-icon-button-size: 36px;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
      direction: var(--direction);
      display: flex;
      align-items: center;
      background-color: var(--mdc-text-field-fill-color, whitesmoke);
      border-bottom-style: solid;
      border-bottom-width: 1px;
    }
    label {
      -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
      -webkit-font-smoothing: var(--ha-font-smoothing);
      font-family: var(
        --mdc-typography-body2-font-family,
        var(--mdc-typography-font-family, var(--ha-font-family-body))
      );
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      line-height: var(
        --mdc-typography-body2-line-height,
        var(--ha-line-height-condensed)
      );
      font-weight: var(
        --mdc-typography-body2-font-weight,
        var(--ha-font-weight-normal)
      );
      letter-spacing: var(
        --mdc-typography-body2-letter-spacing,
        0.0178571429em
      );
      text-decoration: var(--mdc-typography-body2-text-decoration, inherit);
      text-transform: var(--mdc-typography-body2-text-transform, inherit);
      color: var(--mdc-theme-text-primary-on-background, rgba(0, 0, 0, 0.87));
      padding-left: 4px;
      padding-inline-start: 4px;
      padding-inline-end: initial;
    }
    ha-input-helper-text {
      padding-top: 8px;
      line-height: var(--ha-line-height-condensed);
    }
  `)),(0,v.__decorate)([(0,f.MZ)()],M.prototype,"label",void 0),(0,v.__decorate)([(0,f.MZ)()],M.prototype,"helper",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:"auto-validate",type:Boolean})],M.prototype,"autoValidate",void 0),(0,v.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"required",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"format",void 0),(0,v.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"days",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"hours",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"minutes",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"seconds",void 0),(0,v.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"milliseconds",void 0),(0,v.__decorate)([(0,f.MZ)({type:String,attribute:"day-label"})],M.prototype,"dayLabel",void 0),(0,v.__decorate)([(0,f.MZ)({type:String,attribute:"hour-label"})],M.prototype,"hourLabel",void 0),(0,v.__decorate)([(0,f.MZ)({type:String,attribute:"min-label"})],M.prototype,"minLabel",void 0),(0,v.__decorate)([(0,f.MZ)({type:String,attribute:"sec-label"})],M.prototype,"secLabel",void 0),(0,v.__decorate)([(0,f.MZ)({type:String,attribute:"ms-label"})],M.prototype,"millisecLabel",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:"enable-second",type:Boolean})],M.prototype,"enableSecond",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:"enable-millisecond",type:Boolean})],M.prototype,"enableMillisecond",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:"enable-day",type:Boolean})],M.prototype,"enableDay",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:"no-hours-limit",type:Boolean})],M.prototype,"noHoursLimit",void 0),(0,v.__decorate)([(0,f.MZ)({attribute:!1})],M.prototype,"amPm",void 0),(0,v.__decorate)([(0,f.MZ)({type:Boolean,reflect:!0})],M.prototype,"clearable",void 0),M=(0,v.__decorate)([(0,f.EM)("ha-base-time-input")],M)},23152:function(e,t,a){a.r(t),a.d(t,{HaTimeSelector:function(){return c}});var i,o=a(44734),r=a(56038),l=a(69683),d=a(6454),n=(a(28706),a(62826)),s=a(96196),h=a(77845),u=(a(28893),e=>e),c=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(i))).disabled=!1,e.required=!1,e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e;return(0,s.qy)(i||(i=u`
      <ha-time-input
        .value=${0}
        .locale=${0}
        .disabled=${0}
        .required=${0}
        clearable
        .helper=${0}
        .label=${0}
        .enableSecond=${0}
      ></ha-time-input>
    `),"string"==typeof this.value?this.value:void 0,this.hass.locale,this.disabled,this.required,this.helper,this.label,!(null!==(e=this.selector.time)&&void 0!==e&&e.no_second))}}])}(s.WF);(0,n.__decorate)([(0,h.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,n.__decorate)([(0,h.MZ)({attribute:!1})],c.prototype,"selector",void 0),(0,n.__decorate)([(0,h.MZ)()],c.prototype,"value",void 0),(0,n.__decorate)([(0,h.MZ)()],c.prototype,"label",void 0),(0,n.__decorate)([(0,h.MZ)()],c.prototype,"helper",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean})],c.prototype,"disabled",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean})],c.prototype,"required",void 0),c=(0,n.__decorate)([(0,h.EM)("ha-selector-time")],c)},28893:function(e,t,a){var i,o=a(44734),r=a(56038),l=a(69683),d=a(6454),n=(a(28706),a(2892),a(26099),a(38781),a(68156),a(62826)),s=a(96196),h=a(77845),u=a(59006),c=a(92542),p=(a(29261),e=>e),m=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,i=new Array(a),r=0;r<a;r++)i[r]=arguments[r];return(e=(0,l.A)(this,t,[].concat(i))).disabled=!1,e.required=!1,e.enableSecond=!1,e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){var e=(0,u.J)(this.locale),t=NaN,a=NaN,o=NaN,r=0;if(this.value){var l,d=(null===(l=this.value)||void 0===l?void 0:l.split(":"))||[];a=d[1]?Number(d[1]):0,o=d[2]?Number(d[2]):0,(r=t=d[0]?Number(d[0]):0)&&e&&r>12&&r<24&&(t=r-12),e&&0===r&&(t=12)}return(0,s.qy)(i||(i=p`
      <ha-base-time-input
        .label=${0}
        .hours=${0}
        .minutes=${0}
        .seconds=${0}
        .format=${0}
        .amPm=${0}
        .disabled=${0}
        @value-changed=${0}
        .enableSecond=${0}
        .required=${0}
        .clearable=${0}
        .helper=${0}
        day-label="dd"
        hour-label="hh"
        min-label="mm"
        sec-label="ss"
        ms-label="ms"
      ></ha-base-time-input>
    `),this.label,t,a,o,e?12:24,e&&r>=12?"PM":"AM",this.disabled,this._timeChanged,this.enableSecond,this.required,this.clearable&&void 0!==this.value,this.helper)}},{key:"_timeChanged",value:function(e){e.stopPropagation();var t,a=e.detail.value,i=(0,u.J)(this.locale);if(!(void 0===a||isNaN(a.hours)&&isNaN(a.minutes)&&isNaN(a.seconds))){var o=a.hours||0;a&&i&&("PM"===a.amPm&&o<12&&(o+=12),"AM"===a.amPm&&12===o&&(o=0)),t=`${o.toString().padStart(2,"0")}:${a.minutes?a.minutes.toString().padStart(2,"0"):"00"}:${a.seconds?a.seconds.toString().padStart(2,"0"):"00"}`}t!==this.value&&(this.value=t,(0,c.r)(this,"change"),(0,c.r)(this,"value-changed",{value:t}))}}])}(s.WF);(0,n.__decorate)([(0,h.MZ)({attribute:!1})],m.prototype,"locale",void 0),(0,n.__decorate)([(0,h.MZ)()],m.prototype,"value",void 0),(0,n.__decorate)([(0,h.MZ)()],m.prototype,"label",void 0),(0,n.__decorate)([(0,h.MZ)()],m.prototype,"helper",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean})],m.prototype,"disabled",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean})],m.prototype,"required",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean,attribute:"enable-second"})],m.prototype,"enableSecond",void 0),(0,n.__decorate)([(0,h.MZ)({type:Boolean,reflect:!0})],m.prototype,"clearable",void 0),m=(0,n.__decorate)([(0,h.EM)("ha-time-input")],m)}}]);
//# sourceMappingURL=1849.024a6ab8c859de26.js.map