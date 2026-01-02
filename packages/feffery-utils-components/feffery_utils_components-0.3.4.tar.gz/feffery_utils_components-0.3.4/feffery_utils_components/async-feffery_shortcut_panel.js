/*! For license information please see async-feffery_shortcut_panel.js.LICENSE.txt */
(window.webpackJsonpfeffery_utils_components=window.webpackJsonpfeffery_utils_components||[]).push([[30],{1141:function(e,t,i){"use strict";const n=window,s=n.ShadowRoot&&(void 0===n.ShadyCSS||n.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,o=Symbol(),r=new WeakMap;class a{constructor(e,t,i){if(this._$cssResult$=!0,i!==o)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(s&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=r.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&r.set(t,e))}return e}toString(){return this.cssText}}const l=(e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,n)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[n+1],e[0]);return new a(i,e,o)},c=s?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new a("string"==typeof e?e:e+"",void 0,o))(t)})(e):e;var h;const d=window,p=d.trustedTypes,u=p?p.emptyScript:"",_=d.reactiveElementPolyfillSupport,f={toAttribute(e,t){switch(t){case Boolean:e=e?u:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},v=(e,t)=>t!==e&&(t==t||e==e),y={attribute:!0,type:String,converter:f,reflect:!1,hasChanged:v};class m extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu()}static addInitializer(e){var t;this.finalize(),(null!==(t=this.h)&&void 0!==t?t:this.h=[]).push(e)}static get observedAttributes(){this.finalize();const e=[];return this.elementProperties.forEach((t,i)=>{const n=this._$Ep(i,t);void 0!==n&&(this._$Ev.set(n,i),e.push(n))}),e}static createProperty(e,t=y){if(t.state&&(t.attribute=!1),this.finalize(),this.elementProperties.set(e,t),!t.noAccessor&&!this.prototype.hasOwnProperty(e)){const i="symbol"==typeof e?Symbol():"__"+e,n=this.getPropertyDescriptor(e,i,t);void 0!==n&&Object.defineProperty(this.prototype,e,n)}}static getPropertyDescriptor(e,t,i){return{get(){return this[t]},set(n){const s=this[e];this[t]=n,this.requestUpdate(e,s,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)||y}static finalize(){if(this.hasOwnProperty("finalized"))return!1;this.finalized=!0;const e=Object.getPrototypeOf(this);if(e.finalize(),void 0!==e.h&&(this.h=[...e.h]),this.elementProperties=new Map(e.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const e=this.properties,t=[...Object.getOwnPropertyNames(e),...Object.getOwnPropertySymbols(e)];for(const i of t)this.createProperty(i,e[i])}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(c(e))}else void 0!==e&&t.push(c(e));return t}static _$Ep(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}_$Eu(){var e;this._$E_=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(e=this.constructor.h)||void 0===e||e.forEach(e=>e(this))}addController(e){var t,i;(null!==(t=this._$ES)&&void 0!==t?t:this._$ES=[]).push(e),void 0!==this.renderRoot&&this.isConnected&&(null===(i=e.hostConnected)||void 0===i||i.call(e))}removeController(e){var t;null===(t=this._$ES)||void 0===t||t.splice(this._$ES.indexOf(e)>>>0,1)}_$Eg(){this.constructor.elementProperties.forEach((e,t)=>{this.hasOwnProperty(t)&&(this._$Ei.set(t,this[t]),delete this[t])})}createRenderRoot(){var e;const t=null!==(e=this.shadowRoot)&&void 0!==e?e:this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{s?e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet):t.forEach(t=>{const i=document.createElement("style"),s=n.litNonce;void 0!==s&&i.setAttribute("nonce",s),i.textContent=t.cssText,e.appendChild(i)})})(t,this.constructor.elementStyles),t}connectedCallback(){var e;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostConnected)||void 0===t?void 0:t.call(e)})}enableUpdating(e){}disconnectedCallback(){var e;null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostDisconnected)||void 0===t?void 0:t.call(e)})}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$EO(e,t,i=y){var n;const s=this.constructor._$Ep(e,i);if(void 0!==s&&!0===i.reflect){const o=(void 0!==(null===(n=i.converter)||void 0===n?void 0:n.toAttribute)?i.converter:f).toAttribute(t,i.type);this._$El=e,null==o?this.removeAttribute(s):this.setAttribute(s,o),this._$El=null}}_$AK(e,t){var i;const n=this.constructor,s=n._$Ev.get(e);if(void 0!==s&&this._$El!==s){const e=n.getPropertyOptions(s),o="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==(null===(i=e.converter)||void 0===i?void 0:i.fromAttribute)?e.converter:f;this._$El=s,this[s]=o.fromAttribute(t,e.type),this._$El=null}}requestUpdate(e,t,i){let n=!0;void 0!==e&&(((i=i||this.constructor.getPropertyOptions(e)).hasChanged||v)(this[e],t)?(this._$AL.has(e)||this._$AL.set(e,t),!0===i.reflect&&this._$El!==e&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(e,i))):n=!1),!this.isUpdatePending&&n&&(this._$E_=this._$Ej())}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var e;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach((e,t)=>this[t]=e),this._$Ei=void 0);let t=!1;const i=this._$AL;try{t=this.shouldUpdate(i),t?(this.willUpdate(i),null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostUpdate)||void 0===t?void 0:t.call(e)}),this.update(i)):this._$Ek()}catch(e){throw t=!1,this._$Ek(),e}t&&this._$AE(i)}willUpdate(e){}_$AE(e){var t;null===(t=this._$ES)||void 0===t||t.forEach(e=>{var t;return null===(t=e.hostUpdated)||void 0===t?void 0:t.call(e)}),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(e){return!0}update(e){void 0!==this._$EC&&(this._$EC.forEach((e,t)=>this._$EO(t,this[t],e)),this._$EC=void 0),this._$Ek()}updated(e){}firstUpdated(e){}}var g;m.finalized=!0,m.elementProperties=new Map,m.elementStyles=[],m.shadowRootOptions={mode:"open"},null==_||_({ReactiveElement:m}),(null!==(h=d.reactiveElementVersions)&&void 0!==h?h:d.reactiveElementVersions=[]).push("1.6.3");const $=window,b=$.trustedTypes,E=b?b.createPolicy("lit-html",{createHTML:e=>e}):void 0,A=`lit$${(Math.random()+"").slice(9)}$`,w="?"+A,k=`<${w}>`,x=document,P=()=>x.createComment(""),j=e=>null===e||"object"!=typeof e&&"function"!=typeof e,O=Array.isArray,S=e=>O(e)||"function"==typeof(null==e?void 0:e[Symbol.iterator]),C=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,M=/-->/g,D=/>/g,U=RegExp(">|[ \t\n\f\r](?:([^\\s\"'>=/]+)([ \t\n\f\r]*=[ \t\n\f\r]*(?:[^ \t\n\f\r\"'`<>=]|(\"|')|))|$)","g"),H=/'/g,T=/"/g,R=/^(?:script|style|textarea|title)$/i,B=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),L=B(1),I=(B(2),Symbol.for("lit-noChange")),K=Symbol.for("lit-nothing"),N=new WeakMap,z=x.createTreeWalker(x,129,null,!1);function W(e,t){if(!Array.isArray(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==E?E.createHTML(t):t}const V=(e,t)=>{const i=e.length-1,n=[];let s,o=2===t?"<svg>":"",r=C;for(let t=0;t<i;t++){const i=e[t];let a,l,c=-1,h=0;for(;h<i.length&&(r.lastIndex=h,l=r.exec(i),null!==l);)h=r.lastIndex,r===C?"!--"===l[1]?r=M:void 0!==l[1]?r=D:void 0!==l[2]?(R.test(l[2])&&(s=RegExp("</"+l[2],"g")),r=U):void 0!==l[3]&&(r=U):r===U?">"===l[0]?(r=null!=s?s:C,c=-1):void 0===l[1]?c=-2:(c=r.lastIndex-l[2].length,a=l[1],r=void 0===l[3]?U:'"'===l[3]?T:H):r===T||r===H?r=U:r===M||r===D?r=C:(r=U,s=void 0);const d=r===U&&e[t+1].startsWith("/>")?" ":"";o+=r===C?i+k:c>=0?(n.push(a),i.slice(0,c)+"$lit$"+i.slice(c)+A+d):i+A+(-2===c?(n.push(void 0),t):d)}return[W(e,o+(e[i]||"<?>")+(2===t?"</svg>":"")),n]};class q{constructor({strings:e,_$litType$:t},i){let n;this.parts=[];let s=0,o=0;const r=e.length-1,a=this.parts,[l,c]=V(e,t);if(this.el=q.createElement(l,i),z.currentNode=this.el.content,2===t){const e=this.el.content,t=e.firstChild;t.remove(),e.append(...t.childNodes)}for(;null!==(n=z.nextNode())&&a.length<r;){if(1===n.nodeType){if(n.hasAttributes()){const e=[];for(const t of n.getAttributeNames())if(t.endsWith("$lit$")||t.startsWith(A)){const i=c[o++];if(e.push(t),void 0!==i){const e=n.getAttribute(i.toLowerCase()+"$lit$").split(A),t=/([.?@])?(.*)/.exec(i);a.push({type:1,index:s,name:t[2],strings:e,ctor:"."===t[1]?Q:"?"===t[1]?Y:"@"===t[1]?ee:Z})}else a.push({type:6,index:s})}for(const t of e)n.removeAttribute(t)}if(R.test(n.tagName)){const e=n.textContent.split(A),t=e.length-1;if(t>0){n.textContent=b?b.emptyScript:"";for(let i=0;i<t;i++)n.append(e[i],P()),z.nextNode(),a.push({type:2,index:++s});n.append(e[t],P())}}}else if(8===n.nodeType)if(n.data===w)a.push({type:2,index:s});else{let e=-1;for(;-1!==(e=n.data.indexOf(A,e+1));)a.push({type:7,index:s}),e+=A.length-1}s++}}static createElement(e,t){const i=x.createElement("template");return i.innerHTML=e,i}}function F(e,t,i=e,n){var s,o,r,a;if(t===I)return t;let l=void 0!==n?null===(s=i._$Co)||void 0===s?void 0:s[n]:i._$Cl;const c=j(t)?void 0:t._$litDirective$;return(null==l?void 0:l.constructor)!==c&&(null===(o=null==l?void 0:l._$AO)||void 0===o||o.call(l,!1),void 0===c?l=void 0:(l=new c(e),l._$AT(e,i,n)),void 0!==n?(null!==(r=(a=i)._$Co)&&void 0!==r?r:a._$Co=[])[n]=l:i._$Cl=l),void 0!==l&&(t=F(e,l._$AS(e,t.values),l,n)),t}class J{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){var t;const{el:{content:i},parts:n}=this._$AD,s=(null!==(t=null==e?void 0:e.creationScope)&&void 0!==t?t:x).importNode(i,!0);z.currentNode=s;let o=z.nextNode(),r=0,a=0,l=n[0];for(;void 0!==l;){if(r===l.index){let t;2===l.type?t=new G(o,o.nextSibling,this,e):1===l.type?t=new l.ctor(o,l.name,l.strings,this,e):6===l.type&&(t=new te(o,this,e)),this._$AV.push(t),l=n[++a]}r!==(null==l?void 0:l.index)&&(o=z.nextNode(),r++)}return z.currentNode=x,s}v(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class G{constructor(e,t,i,n){var s;this.type=2,this._$AH=K,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=n,this._$Cp=null===(s=null==n?void 0:n.isConnected)||void 0===s||s}get _$AU(){var e,t;return null!==(t=null===(e=this._$AM)||void 0===e?void 0:e._$AU)&&void 0!==t?t:this._$Cp}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===(null==e?void 0:e.nodeType)&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=F(this,e,t),j(e)?e===K||null==e||""===e?(this._$AH!==K&&this._$AR(),this._$AH=K):e!==this._$AH&&e!==I&&this._(e):void 0!==e._$litType$?this.g(e):void 0!==e.nodeType?this.$(e):S(e)?this.T(e):this._(e)}k(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}$(e){this._$AH!==e&&(this._$AR(),this._$AH=this.k(e))}_(e){this._$AH!==K&&j(this._$AH)?this._$AA.nextSibling.data=e:this.$(x.createTextNode(e)),this._$AH=e}g(e){var t;const{values:i,_$litType$:n}=e,s="number"==typeof n?this._$AC(e):(void 0===n.el&&(n.el=q.createElement(W(n.h,n.h[0]),this.options)),n);if((null===(t=this._$AH)||void 0===t?void 0:t._$AD)===s)this._$AH.v(i);else{const e=new J(s,this),t=e.u(this.options);e.v(i),this.$(t),this._$AH=e}}_$AC(e){let t=N.get(e.strings);return void 0===t&&N.set(e.strings,t=new q(e)),t}T(e){O(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,n=0;for(const s of e)n===t.length?t.push(i=new G(this.k(P()),this.k(P()),this,this.options)):i=t[n],i._$AI(s),n++;n<t.length&&(this._$AR(i&&i._$AB.nextSibling,n),t.length=n)}_$AR(e=this._$AA.nextSibling,t){var i;for(null===(i=this._$AP)||void 0===i||i.call(this,!1,!0,t);e&&e!==this._$AB;){const t=e.nextSibling;e.remove(),e=t}}setConnected(e){var t;void 0===this._$AM&&(this._$Cp=e,null===(t=this._$AP)||void 0===t||t.call(this,e))}}class Z{constructor(e,t,i,n,s){this.type=1,this._$AH=K,this._$AN=void 0,this.element=e,this.name=t,this._$AM=n,this.options=s,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=K}get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}_$AI(e,t=this,i,n){const s=this.strings;let o=!1;if(void 0===s)e=F(this,e,t,0),o=!j(e)||e!==this._$AH&&e!==I,o&&(this._$AH=e);else{const n=e;let r,a;for(e=s[0],r=0;r<s.length-1;r++)a=F(this,n[i+r],t,r),a===I&&(a=this._$AH[r]),o||(o=!j(a)||a!==this._$AH[r]),a===K?e=K:e!==K&&(e+=(null!=a?a:"")+s[r+1]),this._$AH[r]=a}o&&!n&&this.j(e)}j(e){e===K?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,null!=e?e:"")}}class Q extends Z{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===K?void 0:e}}const X=b?b.emptyScript:"";class Y extends Z{constructor(){super(...arguments),this.type=4}j(e){e&&e!==K?this.element.setAttribute(this.name,X):this.element.removeAttribute(this.name)}}class ee extends Z{constructor(e,t,i,n,s){super(e,t,i,n,s),this.type=5}_$AI(e,t=this){var i;if((e=null!==(i=F(this,e,t,0))&&void 0!==i?i:K)===I)return;const n=this._$AH,s=e===K&&n!==K||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,o=e!==K&&(n===K||s);s&&this.element.removeEventListener(this.name,this,n),o&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){var t,i;"function"==typeof this._$AH?this._$AH.call(null!==(i=null===(t=this.options)||void 0===t?void 0:t.host)&&void 0!==i?i:this.element,e):this._$AH.handleEvent(e)}}class te{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){F(this,e)}}const ie={O:"$lit$",P:A,A:w,C:1,M:V,L:J,R:S,D:F,I:G,V:Z,H:Y,N:ee,U:Q,F:te},ne=$.litHtmlPolyfillSupport;null==ne||ne(q,G),(null!==(g=$.litHtmlVersions)&&void 0!==g?g:$.litHtmlVersions=[]).push("2.8.0");var se,oe;class re extends m{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){var e,t;const i=super.createRenderRoot();return null!==(e=(t=this.renderOptions).renderBefore)&&void 0!==e||(t.renderBefore=i.firstChild),i}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{var n,s;const o=null!==(n=null==i?void 0:i.renderBefore)&&void 0!==n?n:t;let r=o._$litPart$;if(void 0===r){const e=null!==(s=null==i?void 0:i.renderBefore)&&void 0!==s?s:null;o._$litPart$=r=new G(t.insertBefore(P(),e),e,void 0,null!=i?i:{})}return r._$AI(e),r})(t,this.renderRoot,this.renderOptions)}connectedCallback(){var e;super.connectedCallback(),null===(e=this._$Do)||void 0===e||e.setConnected(!0)}disconnectedCallback(){var e;super.disconnectedCallback(),null===(e=this._$Do)||void 0===e||e.setConnected(!1)}render(){return I}}re.finalized=!0,re._$litElement$=!0,null===(se=globalThis.litElementHydrateSupport)||void 0===se||se.call(globalThis,{LitElement:re});const ae=globalThis.litElementPolyfillSupport;null==ae||ae({LitElement:re});(null!==(oe=globalThis.litElementVersions)&&void 0!==oe?oe:globalThis.litElementVersions=[]).push("3.3.3");const le=e=>t=>"function"==typeof t?((e,t)=>(customElements.define(e,t),t))(e,t):((e,t)=>{const{kind:i,elements:n}=t;return{kind:i,elements:n,finisher(t){customElements.define(e,t)}}})(e,t),ce=(e,t)=>"method"===t.kind&&t.descriptor&&!("value"in t.descriptor)?{...t,finisher(i){i.createProperty(t.key,e)}}:{kind:"field",key:Symbol(),placement:"own",descriptor:{},originalKey:t.key,initializer(){"function"==typeof t.initializer&&(this[t.key]=t.initializer.call(this))},finisher(i){i.createProperty(t.key,e)}};function he(e){return(t,i)=>void 0!==i?((e,t,i)=>{t.constructor.createProperty(i,e)})(e,t,i):ce(e,t)}function de(e){return he({...e,state:!0})}var pe;null===(pe=window.HTMLSlotElement)||void 0===pe||pe.prototype.assignedElements;const ue=1,_e=2,fe=3,ve=4,ye=e=>(...t)=>({_$litDirective$:e,values:t});class me{constructor(e){}get _$AU(){return this._$AM._$AU}_$AT(e,t,i){this._$Ct=e,this._$AM=t,this._$Ci=i}_$AS(e,t){return this.update(e,t)}update(e,t){return this.render(...t)}}const{I:ge}=ie,$e=e=>void 0===e.strings,be=()=>document.createComment(""),Ee=(e,t,i)=>{var n;const s=e._$AA.parentNode,o=void 0===t?e._$AB:t._$AA;if(void 0===i){const t=s.insertBefore(be(),o),n=s.insertBefore(be(),o);i=new ge(t,n,e,e.options)}else{const t=i._$AB.nextSibling,r=i._$AM,a=r!==e;if(a){let t;null===(n=i._$AQ)||void 0===n||n.call(i,e),i._$AM=e,void 0!==i._$AP&&(t=e._$AU)!==r._$AU&&i._$AP(t)}if(t!==o||a){let e=i._$AA;for(;e!==t;){const t=e.nextSibling;s.insertBefore(e,o),e=t}}}return i},Ae=(e,t,i=e)=>(e._$AI(t,i),e),we={},ke=(e,t=we)=>e._$AH=t,xe=e=>{var t;null===(t=e._$AP)||void 0===t||t.call(e,!1,!0);let i=e._$AA;const n=e._$AB.nextSibling;for(;i!==n;){const e=i.nextSibling;i.remove(),i=e}},Pe=(e,t,i)=>{const n=new Map;for(let s=t;s<=i;s++)n.set(e[s],s);return n},je=ye(class extends me{constructor(e){if(super(e),e.type!==_e)throw Error("repeat() can only be used in text expressions")}ct(e,t,i){let n;void 0===i?i=t:void 0!==t&&(n=t);const s=[],o=[];let r=0;for(const t of e)s[r]=n?n(t,r):r,o[r]=i(t,r),r++;return{values:o,keys:s}}render(e,t,i){return this.ct(e,t,i).values}update(e,[t,i,n]){var s;const o=e._$AH,{values:r,keys:a}=this.ct(t,i,n);if(!Array.isArray(o))return this.ut=a,r;const l=null!==(s=this.ut)&&void 0!==s?s:this.ut=[],c=[];let h,d,p=0,u=o.length-1,_=0,f=r.length-1;for(;p<=u&&_<=f;)if(null===o[p])p++;else if(null===o[u])u--;else if(l[p]===a[_])c[_]=Ae(o[p],r[_]),p++,_++;else if(l[u]===a[f])c[f]=Ae(o[u],r[f]),u--,f--;else if(l[p]===a[f])c[f]=Ae(o[p],r[f]),Ee(e,c[f+1],o[p]),p++,f--;else if(l[u]===a[_])c[_]=Ae(o[u],r[_]),Ee(e,o[p],o[u]),u--,_++;else if(void 0===h&&(h=Pe(a,_,f),d=Pe(l,p,u)),h.has(l[p]))if(h.has(l[u])){const t=d.get(a[_]),i=void 0!==t?o[t]:null;if(null===i){const t=Ee(e,o[p]);Ae(t,r[_]),c[_]=t}else c[_]=Ae(i,r[_]),Ee(e,o[p],i),o[t]=null;_++}else xe(o[u]),u--;else xe(o[p]),p++;for(;_<=f;){const t=Ee(e,c[f+1]);Ae(t,r[_]),c[_++]=t}for(;p<=u;){const e=o[p++];null!==e&&xe(e)}return this.ut=a,ke(e,c),I}}),Oe=ye(class extends me{constructor(e){if(super(e),e.type!==fe&&e.type!==ue&&e.type!==ve)throw Error("The `live` directive is not allowed on child or event bindings");if(!$e(e))throw Error("`live` bindings can only contain a single expression")}render(e){return e}update(e,[t]){if(t===I||t===K)return t;const i=e.element,n=e.name;if(e.type===fe){if(t===i[n])return I}else if(e.type===ve){if(!!t===i.hasAttribute(n))return I}else if(e.type===ue&&i.getAttribute(n)===t+"")return I;return ke(e),t}}),Se=(e,t)=>{var i,n;const s=e._$AN;if(void 0===s)return!1;for(const e of s)null===(n=(i=e)._$AO)||void 0===n||n.call(i,t,!1),Se(e,t);return!0},Ce=e=>{let t,i;do{if(void 0===(t=e._$AM))break;i=t._$AN,i.delete(e),e=t}while(0===(null==i?void 0:i.size))},Me=e=>{for(let t;t=e._$AM;e=t){let i=t._$AN;if(void 0===i)t._$AN=i=new Set;else if(i.has(e))break;i.add(e),He(t)}};function De(e){void 0!==this._$AN?(Ce(this),this._$AM=e,Me(this)):this._$AM=e}function Ue(e,t=!1,i=0){const n=this._$AH,s=this._$AN;if(void 0!==s&&0!==s.size)if(t)if(Array.isArray(n))for(let e=i;e<n.length;e++)Se(n[e],!1),Ce(n[e]);else null!=n&&(Se(n,!1),Ce(n));else Se(this,e)}const He=e=>{var t,i,n,s;e.type==_e&&(null!==(t=(n=e)._$AP)&&void 0!==t||(n._$AP=Ue),null!==(i=(s=e)._$AQ)&&void 0!==i||(s._$AQ=De))};class Te extends me{constructor(){super(...arguments),this._$AN=void 0}_$AT(e,t,i){super._$AT(e,t,i),Me(this),this.isConnected=e._$AU}_$AO(e,t=!0){var i,n;e!==this.isConnected&&(this.isConnected=e,e?null===(i=this.reconnected)||void 0===i||i.call(this):null===(n=this.disconnected)||void 0===n||n.call(this)),t&&(Se(this,e),Ce(this))}setValue(e){if($e(this._$Ct))this._$Ct._$AI(e,this);else{const t=[...this._$Ct._$AH];t[this._$Ci]=e,this._$Ct._$AI(t,this,0)}}disconnected(){}reconnected(){}}const Re=()=>new Be;class Be{}const Le=new WeakMap,Ie=ye(class extends Te{render(e){return K}update(e,[t]){var i;const n=t!==this.G;return n&&void 0!==this.G&&this.ot(void 0),(n||this.rt!==this.lt)&&(this.G=t,this.dt=null===(i=e.options)||void 0===i?void 0:i.host,this.ot(this.lt=e.element)),K}ot(e){var t;if("function"==typeof this.G){const i=null!==(t=this.dt)&&void 0!==t?t:globalThis;let n=Le.get(i);void 0===n&&(n=new WeakMap,Le.set(i,n)),void 0!==n.get(this.G)&&this.G.call(this.dt,void 0),n.set(this.G,e),void 0!==e&&this.G.call(this.dt,e)}else this.G.value=e}get rt(){var e,t,i;return"function"==typeof this.G?null===(t=Le.get(null!==(e=this.dt)&&void 0!==e?e:globalThis))||void 0===t?void 0:t.get(this.G):null===(i=this.G)||void 0===i?void 0:i.value}disconnected(){this.rt===this.lt&&this.ot(void 0)}reconnected(){this.ot(this.lt)}}),Ke=ye(class extends me{constructor(e){var t;if(super(e),e.type!==ue||"class"!==e.name||(null===(t=e.strings)||void 0===t?void 0:t.length)>2)throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.")}render(e){return" "+Object.keys(e).filter(t=>e[t]).join(" ")+" "}update(e,[t]){var i,n;if(void 0===this.it){this.it=new Set,void 0!==e.strings&&(this.nt=new Set(e.strings.join(" ").split(/\s/).filter(e=>""!==e)));for(const e in t)t[e]&&!(null===(i=this.nt)||void 0===i?void 0:i.has(e))&&this.it.add(e);return this.render(t)}const s=e.element.classList;this.it.forEach(e=>{e in t||(s.remove(e),this.it.delete(e))});for(const e in t){const i=!!t[e];i===this.it.has(e)||(null===(n=this.nt)||void 0===n?void 0:n.has(e))||(i?(s.add(e),this.it.add(e)):(s.remove(e),this.it.delete(e)))}return I}});var Ne="undefined"!=typeof navigator&&navigator.userAgent.toLowerCase().indexOf("firefox")>0;function ze(e,t,i){e.addEventListener?e.addEventListener(t,i,!1):e.attachEvent&&e.attachEvent("on".concat(t),(function(){i(window.event)}))}function We(e,t){for(var i=t.slice(0,t.length-1),n=0;n<i.length;n++)i[n]=e[i[n].toLowerCase()];return i}function Ve(e){"string"!=typeof e&&(e="");for(var t=(e=e.replace(/\s/g,"")).split(","),i=t.lastIndexOf("");i>=0;)t[i-1]+=",",t.splice(i,1),i=t.lastIndexOf("");return t}for(var qe={backspace:8,tab:9,clear:12,enter:13,return:13,esc:27,escape:27,space:32,left:37,up:38,right:39,down:40,del:46,delete:46,ins:45,insert:45,home:36,end:35,pageup:33,pagedown:34,capslock:20,num_0:96,num_1:97,num_2:98,num_3:99,num_4:100,num_5:101,num_6:102,num_7:103,num_8:104,num_9:105,num_multiply:106,num_add:107,num_enter:108,num_subtract:109,num_decimal:110,num_divide:111,"⇪":20,",":188,".":190,"/":191,"`":192,"-":Ne?173:189,"=":Ne?61:187,";":Ne?59:186,"'":222,"[":219,"]":221,"\\":220},Fe={"⇧":16,shift:16,"⌥":18,alt:18,option:18,"⌃":17,ctrl:17,control:17,"⌘":91,cmd:91,command:91},Je={16:"shiftKey",18:"altKey",17:"ctrlKey",91:"metaKey",shiftKey:16,ctrlKey:17,altKey:18,metaKey:91},Ge={16:!1,18:!1,17:!1,91:!1},Ze={},Qe=1;Qe<20;Qe++)qe["f".concat(Qe)]=111+Qe;var Xe=[],Ye="all",et=[],tt=function(e){return qe[e.toLowerCase()]||Fe[e.toLowerCase()]||e.toUpperCase().charCodeAt(0)};function it(e){Ye=e||"all"}function nt(){return Ye||"all"}var st=function(e){var t=e.key,i=e.scope,n=e.method,s=e.splitKey,o=void 0===s?"+":s;Ve(t).forEach((function(e){var t=e.split(o),s=t.length,r=t[s-1],a="*"===r?"*":tt(r);if(Ze[a]){i||(i=nt());var l=s>1?We(Fe,t):[];Ze[a]=Ze[a].map((function(e){return(!n||e.method===n)&&e.scope===i&&function(e,t){for(var i=e.length>=t.length?e:t,n=e.length>=t.length?t:e,s=!0,o=0;o<i.length;o++)-1===n.indexOf(i[o])&&(s=!1);return s}(e.mods,l)?{}:e}))}}))};function ot(e,t,i){var n;if(t.scope===i||"all"===t.scope){for(var s in n=t.mods.length>0,Ge)Object.prototype.hasOwnProperty.call(Ge,s)&&(!Ge[s]&&t.mods.indexOf(+s)>-1||Ge[s]&&-1===t.mods.indexOf(+s))&&(n=!1);(0!==t.mods.length||Ge[16]||Ge[18]||Ge[17]||Ge[91])&&!n&&"*"!==t.shortcut||!1===t.method(e,t)&&(e.preventDefault?e.preventDefault():e.returnValue=!1,e.stopPropagation&&e.stopPropagation(),e.cancelBubble&&(e.cancelBubble=!0))}}function rt(e){var t=Ze["*"],i=e.keyCode||e.which||e.charCode;if(at.filter.call(this,e)){if(93!==i&&224!==i||(i=91),-1===Xe.indexOf(i)&&229!==i&&Xe.push(i),["ctrlKey","altKey","shiftKey","metaKey"].forEach((function(t){var i=Je[t];e[t]&&-1===Xe.indexOf(i)?Xe.push(i):!e[t]&&Xe.indexOf(i)>-1?Xe.splice(Xe.indexOf(i),1):"metaKey"===t&&e[t]&&3===Xe.length&&(e.ctrlKey||e.shiftKey||e.altKey||(Xe=Xe.slice(Xe.indexOf(i))))})),i in Ge){for(var n in Ge[i]=!0,Fe)Fe[n]===i&&(at[n]=!0);if(!t)return}for(var s in Ge)Object.prototype.hasOwnProperty.call(Ge,s)&&(Ge[s]=e[Je[s]]);e.getModifierState&&(!e.altKey||e.ctrlKey)&&e.getModifierState("AltGraph")&&(-1===Xe.indexOf(17)&&Xe.push(17),-1===Xe.indexOf(18)&&Xe.push(18),Ge[17]=!0,Ge[18]=!0);var o=nt();if(t)for(var r=0;r<t.length;r++)t[r].scope===o&&("keydown"===e.type&&t[r].keydown||"keyup"===e.type&&t[r].keyup)&&ot(e,t[r],o);if(i in Ze)for(var a=0;a<Ze[i].length;a++)if(("keydown"===e.type&&Ze[i][a].keydown||"keyup"===e.type&&Ze[i][a].keyup)&&Ze[i][a].key){for(var l=Ze[i][a],c=l.splitKey,h=l.key.split(c),d=[],p=0;p<h.length;p++)d.push(tt(h[p]));d.sort().join("")===Xe.sort().join("")&&ot(e,l,o)}}}function at(e,t,i){Xe=[];var n=Ve(e),s=[],o="all",r=document,a=0,l=!1,c=!0,h="+";for(void 0===i&&"function"==typeof t&&(i=t),"[object Object]"===Object.prototype.toString.call(t)&&(t.scope&&(o=t.scope),t.element&&(r=t.element),t.keyup&&(l=t.keyup),void 0!==t.keydown&&(c=t.keydown),"string"==typeof t.splitKey&&(h=t.splitKey)),"string"==typeof t&&(o=t);a<n.length;a++)s=[],(e=n[a].split(h)).length>1&&(s=We(Fe,e)),(e="*"===(e=e[e.length-1])?"*":tt(e))in Ze||(Ze[e]=[]),Ze[e].push({keyup:l,keydown:c,scope:o,mods:s,shortcut:n[a],method:i,key:n[a],splitKey:h});void 0!==r&&!function(e){return et.indexOf(e)>-1}(r)&&window&&(et.push(r),ze(r,"keydown",(function(e){rt(e)})),ze(window,"focus",(function(){Xe=[]})),ze(r,"keyup",(function(e){rt(e),function(e){var t=e.keyCode||e.which||e.charCode,i=Xe.indexOf(t);if(i>=0&&Xe.splice(i,1),e.key&&"meta"===e.key.toLowerCase()&&Xe.splice(0,Xe.length),93!==t&&224!==t||(t=91),t in Ge)for(var n in Ge[t]=!1,Fe)Fe[n]===t&&(at[n]=!1)}(e)})))}var lt={setScope:it,getScope:nt,deleteScope:function(e,t){var i,n;for(var s in e||(e=nt()),Ze)if(Object.prototype.hasOwnProperty.call(Ze,s))for(i=Ze[s],n=0;n<i.length;)i[n].scope===e?i.splice(n,1):n++;nt()===e&&it(t||"all")},getPressedKeyCodes:function(){return Xe.slice(0)},isPressed:function(e){return"string"==typeof e&&(e=tt(e)),-1!==Xe.indexOf(e)},filter:function(e){var t=e.target||e.srcElement,i=t.tagName,n=!0;return!t.isContentEditable&&("INPUT"!==i&&"TEXTAREA"!==i&&"SELECT"!==i||t.readOnly)||(n=!1),n},unbind:function(e){if(e){if(Array.isArray(e))e.forEach((function(e){e.key&&st(e)}));else if("object"==typeof e)e.key&&st(e);else if("string"==typeof e){for(var t=arguments.length,i=new Array(t>1?t-1:0),n=1;n<t;n++)i[n-1]=arguments[n];var s=i[0],o=i[1];"function"==typeof s&&(o=s,s=""),st({key:e,scope:s,method:o,splitKey:"+"})}}else Object.keys(Ze).forEach((function(e){return delete Ze[e]}))}};for(var ct in lt)Object.prototype.hasOwnProperty.call(lt,ct)&&(at[ct]=lt[ct]);if("undefined"!=typeof window){var ht=window.hotkeys;at.noConflict=function(e){return e&&window.hotkeys===at&&(window.hotkeys=ht),at},window.hotkeys=at}var dt=at,pt=function(e,t,i,n){var s,o=arguments.length,r=o<3?t:null===n?n=Object.getOwnPropertyDescriptor(t,i):n;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)r=Reflect.decorate(e,t,i,n);else for(var a=e.length-1;a>=0;a--)(s=e[a])&&(r=(o<3?s(r):o>3?s(t,i,r):s(t,i))||r);return o>3&&r&&Object.defineProperty(t,i,r),r};let ut=class extends re{constructor(){super(...arguments),this.placeholder="",this.hideBreadcrumbs=!1,this.breadcrumbHome="Home",this.breadcrumbs=[],this._inputRef=Re()}render(){let e="";if(!this.hideBreadcrumbs){const t=[];for(const e of this.breadcrumbs)t.push(L`<button
            tabindex="-1"
            @click=${()=>this.selectParent(e)}
            class="breadcrumb"
          >
            ${e}
          </button>`);e=L`<div class="breadcrumb-list">
        <button
          tabindex="-1"
          @click=${()=>this.selectParent()}
          class="breadcrumb"
        >
          ${this.breadcrumbHome}
        </button>
        ${t}
      </div>`}return L`
      ${e}
      <div part="ninja-input-wrapper" class="search-wrapper">
        <input
          part="ninja-input"
          type="text"
          id="search"
          spellcheck="false"
          autocomplete="off"
          @input="${this._handleInput}"
          ${Ie(this._inputRef)}
          placeholder="${this.placeholder}"
          class="search"
        />
      </div>
    `}setSearch(e){this._inputRef.value&&(this._inputRef.value.value=e)}focusSearch(){requestAnimationFrame(()=>this._inputRef.value.focus())}_handleInput(e){const t=e.target;this.dispatchEvent(new CustomEvent("change",{detail:{search:t.value},bubbles:!1,composed:!1}))}selectParent(e){this.dispatchEvent(new CustomEvent("setParent",{detail:{parent:e},bubbles:!0,composed:!0}))}firstUpdated(){this.focusSearch()}_close(){this.dispatchEvent(new CustomEvent("close",{bubbles:!0,composed:!0}))}};ut.styles=l`
    :host {
      flex: 1;
      position: relative;
    }
    .search {
      padding: 1.25em;
      flex-grow: 1;
      flex-shrink: 0;
      margin: 0px;
      border: none;
      appearance: none;
      font-size: 1.125em;
      background: transparent;
      caret-color: var(--ninja-accent-color);
      color: var(--ninja-text-color);
      outline: none;
      font-family: var(--ninja-font-family);
    }
    .search::placeholder {
      color: var(--ninja-placeholder-color);
    }
    .breadcrumb-list {
      padding: 1em 4em 0 1em;
      display: flex;
      flex-direction: row;
      align-items: stretch;
      justify-content: flex-start;
      flex: initial;
    }

    .breadcrumb {
      background: var(--ninja-secondary-background-color);
      text-align: center;
      line-height: 1.2em;
      border-radius: var(--ninja-key-border-radius);
      border: 0;
      cursor: pointer;
      padding: 0.1em 0.5em;
      color: var(--ninja-secondary-text-color);
      margin-right: 0.5em;
      outline: none;
      font-family: var(--ninja-font-family);
    }

    .search-wrapper {
      display: flex;
      border-bottom: var(--ninja-separate-border);
    }
  `,pt([he()],ut.prototype,"placeholder",void 0),pt([he({type:Boolean})],ut.prototype,"hideBreadcrumbs",void 0),pt([he()],ut.prototype,"breadcrumbHome",void 0),pt([he({type:Array})],ut.prototype,"breadcrumbs",void 0),ut=pt([le("ninja-header")],ut);class _t extends me{constructor(e){if(super(e),this.et=K,e.type!==_e)throw Error(this.constructor.directiveName+"() can only be used in child bindings")}render(e){if(e===K||null==e)return this.ft=void 0,this.et=e;if(e===I)return e;if("string"!=typeof e)throw Error(this.constructor.directiveName+"() called with a non-string value");if(e===this.et)return this.ft;this.et=e;const t=[e];return t.raw=t,this.ft={_$litType$:this.constructor.resultType,strings:t,values:[]}}}_t.directiveName="unsafeHTML",_t.resultType=1;const ft=ye(_t);var vt=i(2);const yt=window,mt=yt.ShadowRoot&&(void 0===yt.ShadyCSS||yt.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,gt=Symbol(),$t=new WeakMap;class bt{constructor(e,t,i){if(this._$cssResult$=!0,i!==gt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(mt&&void 0===e){const i=void 0!==t&&1===t.length;i&&(e=$t.get(t)),void 0===e&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),i&&$t.set(t,e))}return e}toString(){return this.cssText}}const Et=mt?e=>e:e=>e instanceof CSSStyleSheet?(e=>{let t="";for(const i of e.cssRules)t+=i.cssText;return(e=>new bt("string"==typeof e?e:e+"",void 0,gt))(t)})(e):e;var At;const wt=window,kt=wt.trustedTypes,xt=kt?kt.emptyScript:"",Pt=wt.reactiveElementPolyfillSupport,jt={toAttribute(e,t){switch(t){case Boolean:e=e?xt:null;break;case Object:case Array:e=null==e?e:JSON.stringify(e)}return e},fromAttribute(e,t){let i=e;switch(t){case Boolean:i=null!==e;break;case Number:i=null===e?null:Number(e);break;case Object:case Array:try{i=JSON.parse(e)}catch(e){i=null}}return i}},Ot=(e,t)=>t!==e&&(t==t||e==e),St={attribute:!0,type:String,converter:jt,reflect:!1,hasChanged:Ot};class Ct extends HTMLElement{constructor(){super(),this._$Ei=new Map,this.isUpdatePending=!1,this.hasUpdated=!1,this._$El=null,this._$Eu()}static addInitializer(e){var t;this.finalize(),(null!==(t=this.h)&&void 0!==t?t:this.h=[]).push(e)}static get observedAttributes(){this.finalize();const e=[];return this.elementProperties.forEach((t,i)=>{const n=this._$Ep(i,t);void 0!==n&&(this._$Ev.set(n,i),e.push(n))}),e}static createProperty(e,t=St){if(t.state&&(t.attribute=!1),this.finalize(),this.elementProperties.set(e,t),!t.noAccessor&&!this.prototype.hasOwnProperty(e)){const i="symbol"==typeof e?Symbol():"__"+e,n=this.getPropertyDescriptor(e,i,t);void 0!==n&&Object.defineProperty(this.prototype,e,n)}}static getPropertyDescriptor(e,t,i){return{get(){return this[t]},set(n){const s=this[e];this[t]=n,this.requestUpdate(e,s,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)||St}static finalize(){if(this.hasOwnProperty("finalized"))return!1;this.finalized=!0;const e=Object.getPrototypeOf(this);if(e.finalize(),void 0!==e.h&&(this.h=[...e.h]),this.elementProperties=new Map(e.elementProperties),this._$Ev=new Map,this.hasOwnProperty("properties")){const e=this.properties,t=[...Object.getOwnPropertyNames(e),...Object.getOwnPropertySymbols(e)];for(const i of t)this.createProperty(i,e[i])}return this.elementStyles=this.finalizeStyles(this.styles),!0}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const i=new Set(e.flat(1/0).reverse());for(const e of i)t.unshift(Et(e))}else void 0!==e&&t.push(Et(e));return t}static _$Ep(e,t){const i=t.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof e?e.toLowerCase():void 0}_$Eu(){var e;this._$E_=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$Eg(),this.requestUpdate(),null===(e=this.constructor.h)||void 0===e||e.forEach(e=>e(this))}addController(e){var t,i;(null!==(t=this._$ES)&&void 0!==t?t:this._$ES=[]).push(e),void 0!==this.renderRoot&&this.isConnected&&(null===(i=e.hostConnected)||void 0===i||i.call(e))}removeController(e){var t;null===(t=this._$ES)||void 0===t||t.splice(this._$ES.indexOf(e)>>>0,1)}_$Eg(){this.constructor.elementProperties.forEach((e,t)=>{this.hasOwnProperty(t)&&(this._$Ei.set(t,this[t]),delete this[t])})}createRenderRoot(){var e;const t=null!==(e=this.shadowRoot)&&void 0!==e?e:this.attachShadow(this.constructor.shadowRootOptions);return((e,t)=>{mt?e.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet):t.forEach(t=>{const i=document.createElement("style"),n=yt.litNonce;void 0!==n&&i.setAttribute("nonce",n),i.textContent=t.cssText,e.appendChild(i)})})(t,this.constructor.elementStyles),t}connectedCallback(){var e;void 0===this.renderRoot&&(this.renderRoot=this.createRenderRoot()),this.enableUpdating(!0),null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostConnected)||void 0===t?void 0:t.call(e)})}enableUpdating(e){}disconnectedCallback(){var e;null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostDisconnected)||void 0===t?void 0:t.call(e)})}attributeChangedCallback(e,t,i){this._$AK(e,i)}_$EO(e,t,i=St){var n;const s=this.constructor._$Ep(e,i);if(void 0!==s&&!0===i.reflect){const o=(void 0!==(null===(n=i.converter)||void 0===n?void 0:n.toAttribute)?i.converter:jt).toAttribute(t,i.type);this._$El=e,null==o?this.removeAttribute(s):this.setAttribute(s,o),this._$El=null}}_$AK(e,t){var i;const n=this.constructor,s=n._$Ev.get(e);if(void 0!==s&&this._$El!==s){const e=n.getPropertyOptions(s),o="function"==typeof e.converter?{fromAttribute:e.converter}:void 0!==(null===(i=e.converter)||void 0===i?void 0:i.fromAttribute)?e.converter:jt;this._$El=s,this[s]=o.fromAttribute(t,e.type),this._$El=null}}requestUpdate(e,t,i){let n=!0;void 0!==e&&(((i=i||this.constructor.getPropertyOptions(e)).hasChanged||Ot)(this[e],t)?(this._$AL.has(e)||this._$AL.set(e,t),!0===i.reflect&&this._$El!==e&&(void 0===this._$EC&&(this._$EC=new Map),this._$EC.set(e,i))):n=!1),!this.isUpdatePending&&n&&(this._$E_=this._$Ej())}async _$Ej(){this.isUpdatePending=!0;try{await this._$E_}catch(e){Promise.reject(e)}const e=this.scheduleUpdate();return null!=e&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){var e;if(!this.isUpdatePending)return;this.hasUpdated,this._$Ei&&(this._$Ei.forEach((e,t)=>this[t]=e),this._$Ei=void 0);let t=!1;const i=this._$AL;try{t=this.shouldUpdate(i),t?(this.willUpdate(i),null===(e=this._$ES)||void 0===e||e.forEach(e=>{var t;return null===(t=e.hostUpdate)||void 0===t?void 0:t.call(e)}),this.update(i)):this._$Ek()}catch(e){throw t=!1,this._$Ek(),e}t&&this._$AE(i)}willUpdate(e){}_$AE(e){var t;null===(t=this._$ES)||void 0===t||t.forEach(e=>{var t;return null===(t=e.hostUpdated)||void 0===t?void 0:t.call(e)}),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$Ek(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$E_}shouldUpdate(e){return!0}update(e){void 0!==this._$EC&&(this._$EC.forEach((e,t)=>this._$EO(t,this[t],e)),this._$EC=void 0),this._$Ek()}updated(e){}firstUpdated(e){}}var Mt;Ct.finalized=!0,Ct.elementProperties=new Map,Ct.elementStyles=[],Ct.shadowRootOptions={mode:"open"},null==Pt||Pt({ReactiveElement:Ct}),(null!==(At=wt.reactiveElementVersions)&&void 0!==At?At:wt.reactiveElementVersions=[]).push("1.6.3");const Dt=window,Ut=Dt.trustedTypes,Ht=Ut?Ut.createPolicy("lit-html",{createHTML:e=>e}):void 0,Tt=`lit$${(Math.random()+"").slice(9)}$`,Rt="?"+Tt,Bt=`<${Rt}>`,Lt=document,It=()=>Lt.createComment(""),Kt=e=>null===e||"object"!=typeof e&&"function"!=typeof e,Nt=Array.isArray,zt=e=>Nt(e)||"function"==typeof(null==e?void 0:e[Symbol.iterator]),Wt=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Vt=/-->/g,qt=/>/g,Ft=RegExp(">|[ \t\n\f\r](?:([^\\s\"'>=/]+)([ \t\n\f\r]*=[ \t\n\f\r]*(?:[^ \t\n\f\r\"'`<>=]|(\"|')|))|$)","g"),Jt=/'/g,Gt=/"/g,Zt=/^(?:script|style|textarea|title)$/i,Qt=e=>(t,...i)=>({_$litType$:e,strings:t,values:i}),Xt=Qt(1),Yt=(Qt(2),Symbol.for("lit-noChange")),ei=Symbol.for("lit-nothing"),ti=new WeakMap,ii=Lt.createTreeWalker(Lt,129,null,!1);function ni(e,t){if(!Array.isArray(e)||!e.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==Ht?Ht.createHTML(t):t}const si=(e,t)=>{const i=e.length-1,n=[];let s,o=2===t?"<svg>":"",r=Wt;for(let t=0;t<i;t++){const i=e[t];let a,l,c=-1,h=0;for(;h<i.length&&(r.lastIndex=h,l=r.exec(i),null!==l);)h=r.lastIndex,r===Wt?"!--"===l[1]?r=Vt:void 0!==l[1]?r=qt:void 0!==l[2]?(Zt.test(l[2])&&(s=RegExp("</"+l[2],"g")),r=Ft):void 0!==l[3]&&(r=Ft):r===Ft?">"===l[0]?(r=null!=s?s:Wt,c=-1):void 0===l[1]?c=-2:(c=r.lastIndex-l[2].length,a=l[1],r=void 0===l[3]?Ft:'"'===l[3]?Gt:Jt):r===Gt||r===Jt?r=Ft:r===Vt||r===qt?r=Wt:(r=Ft,s=void 0);const d=r===Ft&&e[t+1].startsWith("/>")?" ":"";o+=r===Wt?i+Bt:c>=0?(n.push(a),i.slice(0,c)+"$lit$"+i.slice(c)+Tt+d):i+Tt+(-2===c?(n.push(void 0),t):d)}return[ni(e,o+(e[i]||"<?>")+(2===t?"</svg>":"")),n]};class oi{constructor({strings:e,_$litType$:t},i){let n;this.parts=[];let s=0,o=0;const r=e.length-1,a=this.parts,[l,c]=si(e,t);if(this.el=oi.createElement(l,i),ii.currentNode=this.el.content,2===t){const e=this.el.content,t=e.firstChild;t.remove(),e.append(...t.childNodes)}for(;null!==(n=ii.nextNode())&&a.length<r;){if(1===n.nodeType){if(n.hasAttributes()){const e=[];for(const t of n.getAttributeNames())if(t.endsWith("$lit$")||t.startsWith(Tt)){const i=c[o++];if(e.push(t),void 0!==i){const e=n.getAttribute(i.toLowerCase()+"$lit$").split(Tt),t=/([.?@])?(.*)/.exec(i);a.push({type:1,index:s,name:t[2],strings:e,ctor:"."===t[1]?hi:"?"===t[1]?pi:"@"===t[1]?ui:ci})}else a.push({type:6,index:s})}for(const t of e)n.removeAttribute(t)}if(Zt.test(n.tagName)){const e=n.textContent.split(Tt),t=e.length-1;if(t>0){n.textContent=Ut?Ut.emptyScript:"";for(let i=0;i<t;i++)n.append(e[i],It()),ii.nextNode(),a.push({type:2,index:++s});n.append(e[t],It())}}}else if(8===n.nodeType)if(n.data===Rt)a.push({type:2,index:s});else{let e=-1;for(;-1!==(e=n.data.indexOf(Tt,e+1));)a.push({type:7,index:s}),e+=Tt.length-1}s++}}static createElement(e,t){const i=Lt.createElement("template");return i.innerHTML=e,i}}function ri(e,t,i=e,n){var s,o,r,a;if(t===Yt)return t;let l=void 0!==n?null===(s=i._$Co)||void 0===s?void 0:s[n]:i._$Cl;const c=Kt(t)?void 0:t._$litDirective$;return(null==l?void 0:l.constructor)!==c&&(null===(o=null==l?void 0:l._$AO)||void 0===o||o.call(l,!1),void 0===c?l=void 0:(l=new c(e),l._$AT(e,i,n)),void 0!==n?(null!==(r=(a=i)._$Co)&&void 0!==r?r:a._$Co=[])[n]=l:i._$Cl=l),void 0!==l&&(t=ri(e,l._$AS(e,t.values),l,n)),t}class ai{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){var t;const{el:{content:i},parts:n}=this._$AD,s=(null!==(t=null==e?void 0:e.creationScope)&&void 0!==t?t:Lt).importNode(i,!0);ii.currentNode=s;let o=ii.nextNode(),r=0,a=0,l=n[0];for(;void 0!==l;){if(r===l.index){let t;2===l.type?t=new li(o,o.nextSibling,this,e):1===l.type?t=new l.ctor(o,l.name,l.strings,this,e):6===l.type&&(t=new _i(o,this,e)),this._$AV.push(t),l=n[++a]}r!==(null==l?void 0:l.index)&&(o=ii.nextNode(),r++)}return ii.currentNode=Lt,s}v(e){let t=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(e,i,t),t+=i.strings.length-2):i._$AI(e[t])),t++}}class li{constructor(e,t,i,n){var s;this.type=2,this._$AH=ei,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=i,this.options=n,this._$Cp=null===(s=null==n?void 0:n.isConnected)||void 0===s||s}get _$AU(){var e,t;return null!==(t=null===(e=this._$AM)||void 0===e?void 0:e._$AU)&&void 0!==t?t:this._$Cp}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return void 0!==t&&11===(null==e?void 0:e.nodeType)&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=ri(this,e,t),Kt(e)?e===ei||null==e||""===e?(this._$AH!==ei&&this._$AR(),this._$AH=ei):e!==this._$AH&&e!==Yt&&this._(e):void 0!==e._$litType$?this.g(e):void 0!==e.nodeType?this.$(e):zt(e)?this.T(e):this._(e)}k(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}$(e){this._$AH!==e&&(this._$AR(),this._$AH=this.k(e))}_(e){this._$AH!==ei&&Kt(this._$AH)?this._$AA.nextSibling.data=e:this.$(Lt.createTextNode(e)),this._$AH=e}g(e){var t;const{values:i,_$litType$:n}=e,s="number"==typeof n?this._$AC(e):(void 0===n.el&&(n.el=oi.createElement(ni(n.h,n.h[0]),this.options)),n);if((null===(t=this._$AH)||void 0===t?void 0:t._$AD)===s)this._$AH.v(i);else{const e=new ai(s,this),t=e.u(this.options);e.v(i),this.$(t),this._$AH=e}}_$AC(e){let t=ti.get(e.strings);return void 0===t&&ti.set(e.strings,t=new oi(e)),t}T(e){Nt(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let i,n=0;for(const s of e)n===t.length?t.push(i=new li(this.k(It()),this.k(It()),this,this.options)):i=t[n],i._$AI(s),n++;n<t.length&&(this._$AR(i&&i._$AB.nextSibling,n),t.length=n)}_$AR(e=this._$AA.nextSibling,t){var i;for(null===(i=this._$AP)||void 0===i||i.call(this,!1,!0,t);e&&e!==this._$AB;){const t=e.nextSibling;e.remove(),e=t}}setConnected(e){var t;void 0===this._$AM&&(this._$Cp=e,null===(t=this._$AP)||void 0===t||t.call(this,e))}}class ci{constructor(e,t,i,n,s){this.type=1,this._$AH=ei,this._$AN=void 0,this.element=e,this.name=t,this._$AM=n,this.options=s,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=ei}get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}_$AI(e,t=this,i,n){const s=this.strings;let o=!1;if(void 0===s)e=ri(this,e,t,0),o=!Kt(e)||e!==this._$AH&&e!==Yt,o&&(this._$AH=e);else{const n=e;let r,a;for(e=s[0],r=0;r<s.length-1;r++)a=ri(this,n[i+r],t,r),a===Yt&&(a=this._$AH[r]),o||(o=!Kt(a)||a!==this._$AH[r]),a===ei?e=ei:e!==ei&&(e+=(null!=a?a:"")+s[r+1]),this._$AH[r]=a}o&&!n&&this.j(e)}j(e){e===ei?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,null!=e?e:"")}}class hi extends ci{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===ei?void 0:e}}const di=Ut?Ut.emptyScript:"";class pi extends ci{constructor(){super(...arguments),this.type=4}j(e){e&&e!==ei?this.element.setAttribute(this.name,di):this.element.removeAttribute(this.name)}}class ui extends ci{constructor(e,t,i,n,s){super(e,t,i,n,s),this.type=5}_$AI(e,t=this){var i;if((e=null!==(i=ri(this,e,t,0))&&void 0!==i?i:ei)===Yt)return;const n=this._$AH,s=e===ei&&n!==ei||e.capture!==n.capture||e.once!==n.once||e.passive!==n.passive,o=e!==ei&&(n===ei||s);s&&this.element.removeEventListener(this.name,this,n),o&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){var t,i;"function"==typeof this._$AH?this._$AH.call(null!==(i=null===(t=this.options)||void 0===t?void 0:t.host)&&void 0!==i?i:this.element,e):this._$AH.handleEvent(e)}}class _i{constructor(e,t,i){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(e){ri(this,e)}}const fi=Dt.litHtmlPolyfillSupport;null==fi||fi(oi,li),(null!==(Mt=Dt.litHtmlVersions)&&void 0!==Mt?Mt:Dt.litHtmlVersions=[]).push("2.8.0");var vi,yi;class mi extends Ct{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){var e,t;const i=super.createRenderRoot();return null!==(e=(t=this.renderOptions).renderBefore)&&void 0!==e||(t.renderBefore=i.firstChild),i}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=((e,t,i)=>{var n,s;const o=null!==(n=null==i?void 0:i.renderBefore)&&void 0!==n?n:t;let r=o._$litPart$;if(void 0===r){const e=null!==(s=null==i?void 0:i.renderBefore)&&void 0!==s?s:null;o._$litPart$=r=new li(t.insertBefore(It(),e),e,void 0,null!=i?i:{})}return r._$AI(e),r})(t,this.renderRoot,this.renderOptions)}connectedCallback(){var e;super.connectedCallback(),null===(e=this._$Do)||void 0===e||e.setConnected(!0)}disconnectedCallback(){var e;super.disconnectedCallback(),null===(e=this._$Do)||void 0===e||e.setConnected(!1)}render(){return Yt}}mi.finalized=!0,mi._$litElement$=!0,null===(vi=globalThis.litElementHydrateSupport)||void 0===vi||vi.call(globalThis,{LitElement:mi});const gi=globalThis.litElementPolyfillSupport;null==gi||gi({LitElement:mi});(null!==(yi=globalThis.litElementVersions)&&void 0!==yi?yi:globalThis.litElementVersions=[]).push("3.3.3");var $i;null===($i=window.HTMLSlotElement)||void 0===$i||$i.prototype.assignedElements;const bi=((e,...t)=>{const i=1===e.length?e[0]:t.reduce((t,i,n)=>t+(e=>{if(!0===e._$cssResult$)return e.cssText;if("number"==typeof e)return e;throw Error("Value passed to 'css' function must be a 'css' function result: "+e+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+e[n+1],e[0]);return new bt(i,e,gt)})`:host{font-family:var(--mdc-icon-font, "Material Icons");font-weight:normal;font-style:normal;font-size:var(--mdc-icon-size, 24px);line-height:1;letter-spacing:normal;text-transform:none;display:inline-block;white-space:nowrap;word-wrap:normal;direction:ltr;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;-moz-osx-font-smoothing:grayscale;font-feature-settings:"liga"}`;let Ei=class extends mi{render(){return Xt`<span><slot></slot></span>`}};var Ai;Ei.styles=[bi],Ei=Object(vt.c)([(Ai="mwc-icon",e=>"function"==typeof e?((e,t)=>(customElements.define(e,t),t))(Ai,e):((e,t)=>{const{kind:i,elements:n}=t;return{kind:i,elements:n,finisher(t){customElements.define(e,t)}}})(Ai,e))],Ei);var wi=function(e,t,i,n){var s,o=arguments.length,r=o<3?t:null===n?n=Object.getOwnPropertyDescriptor(t,i):n;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)r=Reflect.decorate(e,t,i,n);else for(var a=e.length-1;a>=0;a--)(s=e[a])&&(r=(o<3?s(r):o>3?s(t,i,r):s(t,i))||r);return o>3&&r&&Object.defineProperty(t,i,r),r};let ki=class extends re{constructor(){super(),this.selected=!1,this.hotKeysJoinedView=!0,this.addEventListener("click",this.click)}ensureInView(){requestAnimationFrame(()=>this.scrollIntoView({block:"nearest"}))}click(){this.dispatchEvent(new CustomEvent("actionsSelected",{detail:this.action,bubbles:!0,composed:!0}))}updated(e){e.has("selected")&&this.selected&&this.ensureInView()}render(){let e,t;this.action.mdIcon?e=L`<mwc-icon part="ninja-icon" class="ninja-icon"
        >${this.action.mdIcon}</mwc-icon
      >`:this.action.icon&&(e=ft(this.action.icon||"")),this.action.hotkey&&(t=this.hotKeysJoinedView?this.action.hotkey.split(",").map(e=>{const t=e.split("+"),i=L`${function*(e,t){const i="function"==typeof t;if(void 0!==e){let n=-1;for(const s of e)n>-1&&(yield i?t(n):t),n++,yield s}}(t.map(e=>L`<kbd>${e}</kbd>`),"+")}`;return L`<div class="ninja-hotkey ninja-hotkeys">
            ${i}
          </div>`}):this.action.hotkey.split(",").map(e=>{const t=e.split("+").map(e=>L`<kbd class="ninja-hotkey">${e}</kbd>`);return L`<kbd class="ninja-hotkeys">${t}</kbd>`}));const i={selected:this.selected,"ninja-action":!0};return L`
      <div
        class="ninja-action"
        part="ninja-action ${this.selected?"ninja-selected":""}"
        class=${Ke(i)}
      >
        ${e}
        <div class="ninja-title">${this.action.title}</div>
        ${t}
      </div>
    `}};ki.styles=l`
    :host {
      display: flex;
      width: 100%;
    }
    .ninja-action {
      padding: 0.75em 1em;
      display: flex;
      border-left: 2px solid transparent;
      align-items: center;
      justify-content: start;
      outline: none;
      transition: color 0s ease 0s;
      width: 100%;
    }
    .ninja-action.selected {
      cursor: pointer;
      color: var(--ninja-selected-text-color);
      background-color: var(--ninja-selected-background);
      border-left: 2px solid var(--ninja-accent-color);
      outline: none;
    }
    .ninja-action.selected .ninja-icon {
      color: var(--ninja-selected-text-color);
    }
    .ninja-icon {
      font-size: var(--ninja-icon-size);
      max-width: var(--ninja-icon-size);
      max-height: var(--ninja-icon-size);
      margin-right: 1em;
      color: var(--ninja-icon-color);
      margin-right: 1em;
      position: relative;
    }

    .ninja-title {
      flex-shrink: 0.01;
      margin-right: 0.5em;
      flex-grow: 1;
      font-size: 0.8125em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .ninja-hotkeys {
      flex-shrink: 0;
      width: min-content;
      display: flex;
    }

    .ninja-hotkeys kbd {
      font-family: inherit;
    }
    .ninja-hotkey {
      background: var(--ninja-secondary-background-color);
      padding: 0.06em 0.25em;
      border-radius: var(--ninja-key-border-radius);
      text-transform: capitalize;
      color: var(--ninja-secondary-text-color);
      font-size: 0.75em;
      font-family: inherit;
    }

    .ninja-hotkey + .ninja-hotkey {
      margin-left: 0.5em;
    }
    .ninja-hotkeys + .ninja-hotkeys {
      margin-left: 1em;
    }
  `,wi([he({type:Object})],ki.prototype,"action",void 0),wi([he({type:Boolean})],ki.prototype,"selected",void 0),wi([he({type:Boolean})],ki.prototype,"hotKeysJoinedView",void 0),ki=wi([le("ninja-action")],ki);const xi=L` <div class="modal-footer" slot="footer">
  <span class="help">
    <svg
      version="1.0"
      class="ninja-examplekey"
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 1280 1280"
    >
      <path
        d="M1013 376c0 73.4-.4 113.3-1.1 120.2a159.9 159.9 0 0 1-90.2 127.3c-20 9.6-36.7 14-59.2 15.5-7.1.5-121.9.9-255 1h-242l95.5-95.5 95.5-95.5-38.3-38.2-38.2-38.3-160 160c-88 88-160 160.4-160 161 0 .6 72 73 160 161l160 160 38.2-38.3 38.3-38.2-95.5-95.5-95.5-95.5h251.1c252.9 0 259.8-.1 281.4-3.6 72.1-11.8 136.9-54.1 178.5-116.4 8.6-12.9 22.6-40.5 28-55.4 4.4-12 10.7-36.1 13.1-50.6 1.6-9.6 1.8-21 2.1-132.8l.4-122.2H1013v110z"
      />
    </svg>

    to select
  </span>
  <span class="help">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="ninja-examplekey"
      viewBox="0 0 24 24"
    >
      <path d="M0 0h24v24H0V0z" fill="none" />
      <path
        d="M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z"
      />
    </svg>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="ninja-examplekey"
      viewBox="0 0 24 24"
    >
      <path d="M0 0h24v24H0V0z" fill="none" />
      <path d="M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z" />
    </svg>
    to navigate
  </span>
  <span class="help">
    <span class="ninja-examplekey esc">esc</span>
    to close
  </span>
  <span class="help">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="ninja-examplekey backspace"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fill-rule="evenodd"
        d="M6.707 4.879A3 3 0 018.828 4H15a3 3 0 013 3v6a3 3 0 01-3 3H8.828a3 3 0 01-2.12-.879l-4.415-4.414a1 1 0 010-1.414l4.414-4.414zm4 2.414a1 1 0 00-1.414 1.414L10.586 10l-1.293 1.293a1 1 0 101.414 1.414L12 11.414l1.293 1.293a1 1 0 001.414-1.414L13.414 10l1.293-1.293a1 1 0 00-1.414-1.414L12 8.586l-1.293-1.293z"
        clip-rule="evenodd"
      />
    </svg>
    move to parent
  </span>
</div>`,Pi=l`
  :host {
    --ninja-width: 640px;
    --ninja-backdrop-filter: none;
    --ninja-overflow-background: rgba(255, 255, 255, 0.5);
    --ninja-text-color: rgb(60, 65, 73);
    --ninja-font-size: 16px;
    --ninja-top: 20%;

    --ninja-key-border-radius: 0.25em;
    --ninja-accent-color: rgb(110, 94, 210);
    --ninja-secondary-background-color: rgb(239, 241, 244);
    --ninja-secondary-text-color: rgb(107, 111, 118);

    --ninja-selected-background: rgb(248, 249, 251);

    --ninja-icon-color: var(--ninja-secondary-text-color);
    --ninja-icon-size: 1.2em;
    --ninja-separate-border: 1px solid var(--ninja-secondary-background-color);

    --ninja-modal-background: #fff;
    --ninja-modal-shadow: rgb(0 0 0 / 50%) 0px 16px 70px;

    --ninja-actions-height: 300px;
    --ninja-group-text-color: rgb(144, 149, 157);

    --ninja-footer-background: rgba(242, 242, 242, 0.4);

    --ninja-placeholder-color: #8e8e8e;

    font-size: var(--ninja-font-size);

    --ninja-z-index: 1;
  }

  :host(.dark) {
    --ninja-backdrop-filter: none;
    --ninja-overflow-background: rgba(0, 0, 0, 0.7);
    --ninja-text-color: #7d7d7d;

    --ninja-modal-background: rgba(17, 17, 17, 0.85);
    --ninja-accent-color: rgb(110, 94, 210);
    --ninja-secondary-background-color: rgba(51, 51, 51, 0.44);
    --ninja-secondary-text-color: #888;

    --ninja-selected-text-color: #eaeaea;
    --ninja-selected-background: rgba(51, 51, 51, 0.44);

    --ninja-icon-color: var(--ninja-secondary-text-color);
    --ninja-separate-border: 1px solid var(--ninja-secondary-background-color);

    --ninja-modal-shadow: 0 16px 70px rgba(0, 0, 0, 0.2);

    --ninja-group-text-color: rgb(144, 149, 157);

    --ninja-footer-background: rgba(30, 30, 30, 85%);
  }

  .modal {
    display: none;
    position: fixed;
    z-index: var(--ninja-z-index);
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background: var(--ninja-overflow-background);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    -webkit-backdrop-filter: var(--ninja-backdrop-filter);
    backdrop-filter: var(--ninja-backdrop-filter);
    text-align: left;
    color: var(--ninja-text-color);
    font-family: var(--ninja-font-family);
  }
  .modal.visible {
    display: block;
  }

  .modal-content {
    position: relative;
    top: var(--ninja-top);
    margin: auto;
    padding: 0;
    display: flex;
    flex-direction: column;
    flex-shrink: 1;
    -webkit-box-flex: 1;
    flex-grow: 1;
    min-width: 0px;
    will-change: transform;
    background: var(--ninja-modal-background);
    border-radius: 0.5em;
    box-shadow: var(--ninja-modal-shadow);
    max-width: var(--ninja-width);
    overflow: hidden;
  }

  .bump {
    animation: zoom-in-zoom-out 0.2s ease;
  }

  @keyframes zoom-in-zoom-out {
    0% {
      transform: scale(0.99);
    }
    50% {
      transform: scale(1.01, 1.01);
    }
    100% {
      transform: scale(1, 1);
    }
  }

  .ninja-github {
    color: var(--ninja-keys-text-color);
    font-weight: normal;
    text-decoration: none;
  }

  .actions-list {
    max-height: var(--ninja-actions-height);
    overflow: auto;
    scroll-behavior: smooth;
    position: relative;
    margin: 0;
    padding: 0.5em 0;
    list-style: none;
    scroll-behavior: smooth;
  }

  .group-header {
    height: 1.375em;
    line-height: 1.375em;
    padding-left: 1.25em;
    padding-top: 0.5em;
    text-overflow: ellipsis;
    white-space: nowrap;
    overflow: hidden;
    font-size: 0.75em;
    line-height: 1em;
    color: var(--ninja-group-text-color);
    margin: 1px 0;
  }

  .modal-footer {
    background: var(--ninja-footer-background);
    padding: 0.5em 1em;
    display: flex;
    /* font-size: 0.75em; */
    border-top: var(--ninja-separate-border);
    color: var(--ninja-secondary-text-color);
  }

  .modal-footer .help {
    display: flex;
    margin-right: 1em;
    align-items: center;
    font-size: 0.75em;
  }

  .ninja-examplekey {
    background: var(--ninja-secondary-background-color);
    padding: 0.06em 0.25em;
    border-radius: var(--ninja-key-border-radius);
    color: var(--ninja-secondary-text-color);
    width: 1em;
    height: 1em;
    margin-right: 0.5em;
    font-size: 1.25em;
    fill: currentColor;
  }
  .ninja-examplekey.esc {
    width: auto;
    height: auto;
    font-size: 1.1em;
  }
  .ninja-examplekey.backspace {
    opacity: 0.7;
  }
`;var ji=function(e,t,i,n){var s,o=arguments.length,r=o<3?t:null===n?n=Object.getOwnPropertyDescriptor(t,i):n;if("object"==typeof Reflect&&"function"==typeof Reflect.decorate)r=Reflect.decorate(e,t,i,n);else for(var a=e.length-1;a>=0;a--)(s=e[a])&&(r=(o<3?s(r):o>3?s(t,i,r):s(t,i))||r);return o>3&&r&&Object.defineProperty(t,i,r),r};let Oi=class extends re{constructor(){super(...arguments),this.placeholder="Type a command or search...",this.disableHotkeys=!1,this.hideBreadcrumbs=!1,this.openHotkey="cmd+k,ctrl+k",this.navigationUpHotkey="up,shift+tab",this.navigationDownHotkey="down,tab",this.closeHotkey="esc",this.goBackHotkey="backspace",this.selectHotkey="enter",this.hotKeysJoinedView=!1,this.noAutoLoadMdIcons=!1,this.data=[],this.visible=!1,this._bump=!0,this._actionMatches=[],this._search="",this._flatData=[],this._headerRef=Re()}open(e={}){this._bump=!0,this.visible=!0,this._headerRef.value.focusSearch(),this._actionMatches.length>0&&(this._selected=this._actionMatches[0]),this.setParent(e.parent)}close(){this._bump=!1,this.visible=!1}setParent(e){this._currentRoot=e||void 0,this._selected=void 0,this._search="",this._headerRef.value.setSearch("")}get breadcrumbs(){var e;const t=[];let i=null===(e=this._selected)||void 0===e?void 0:e.parent;if(i)for(t.push(i);i;){const e=this._flatData.find(e=>e.id===i);(null==e?void 0:e.parent)&&t.push(e.parent),i=e?e.parent:void 0}return t.reverse()}connectedCallback(){super.connectedCallback(),this.noAutoLoadMdIcons||document.fonts.load("24px Material Icons","apps").then(()=>{}),this._registerInternalHotkeys()}disconnectedCallback(){super.disconnectedCallback(),this._unregisterInternalHotkeys()}_flattern(e,t){let i=[];return e||(e=[]),e.map(e=>{const n=e.children&&e.children.some(e=>"string"==typeof e),s={...e,parent:e.parent||t};return n||(s.children&&s.children.length&&(t=e.id,i=[...i,...s.children]),s.children=s.children?s.children.map(e=>e.id):[]),s}).concat(i.length?this._flattern(i,t):i)}update(e){e.has("data")&&!this.disableHotkeys&&(this._flatData=this._flattern(this.data),this._flatData.filter(e=>!!e.hotkey).forEach(e=>{dt(e.hotkey,t=>{t.preventDefault(),e.handler&&e.handler(e)})})),super.update(e)}_registerInternalHotkeys(){this.openHotkey&&dt(this.openHotkey,e=>{e.preventDefault(),this.visible?this.close():this.open()}),this.selectHotkey&&dt(this.selectHotkey,e=>{this.visible&&(e.preventDefault(),this._actionSelected(this._actionMatches[this._selectedIndex]))}),this.goBackHotkey&&dt(this.goBackHotkey,e=>{this.visible&&(this._search||(e.preventDefault(),this._goBack()))}),this.navigationDownHotkey&&dt(this.navigationDownHotkey,e=>{this.visible&&(e.preventDefault(),this._selectedIndex>=this._actionMatches.length-1?this._selected=this._actionMatches[0]:this._selected=this._actionMatches[this._selectedIndex+1])}),this.navigationUpHotkey&&dt(this.navigationUpHotkey,e=>{this.visible&&(e.preventDefault(),0===this._selectedIndex?this._selected=this._actionMatches[this._actionMatches.length-1]:this._selected=this._actionMatches[this._selectedIndex-1])}),this.closeHotkey&&dt(this.closeHotkey,()=>{this.visible&&this.close()})}_unregisterInternalHotkeys(){this.openHotkey&&dt.unbind(this.openHotkey),this.selectHotkey&&dt.unbind(this.selectHotkey),this.goBackHotkey&&dt.unbind(this.goBackHotkey),this.navigationDownHotkey&&dt.unbind(this.navigationDownHotkey),this.navigationUpHotkey&&dt.unbind(this.navigationUpHotkey),this.closeHotkey&&dt.unbind(this.closeHotkey)}_actionFocused(e,t){this._selected=e,t.target.ensureInView()}_onTransitionEnd(){this._bump=!1}_goBack(){const e=this.breadcrumbs.length>1?this.breadcrumbs[this.breadcrumbs.length-2]:void 0;this.setParent(e)}render(){const e={bump:this._bump,"modal-content":!0},t={visible:this.visible,modal:!0},i=this._flatData.filter(e=>{var t;const i=new RegExp(this._search,"gi"),n=e.title.match(i)||(null===(t=e.keywords)||void 0===t?void 0:t.match(i));return(!this._currentRoot&&this._search||e.parent===this._currentRoot)&&n}).reduce((e,t)=>e.set(t.section,[...e.get(t.section)||[],t]),new Map);this._actionMatches=[...i.values()].flat(),this._actionMatches.length>0&&-1===this._selectedIndex&&(this._selected=this._actionMatches[0]),0===this._actionMatches.length&&(this._selected=void 0);const n=e=>L` ${je(e,e=>e.id,e=>{var t;return L`<ninja-action
            exportparts="ninja-action,ninja-selected,ninja-icon"
            .selected=${Oe(e.id===(null===(t=this._selected)||void 0===t?void 0:t.id))}
            .hotKeysJoinedView=${this.hotKeysJoinedView}
            @mouseover=${t=>this._actionFocused(e,t)}
            @actionsSelected=${e=>this._actionSelected(e.detail)}
            .action=${e}
          ></ninja-action>`})}`,s=[];return i.forEach((e,t)=>{const i=t?L`<div class="group-header">${t}</div>`:void 0;s.push(L`${i}${n(e)}`)}),L`
      <div @click=${this._overlayClick} class=${Ke(t)}>
        <div class=${Ke(e)} @animationend=${this._onTransitionEnd}>
          <ninja-header
            exportparts="ninja-input,ninja-input-wrapper"
            ${Ie(this._headerRef)}
            .placeholder=${this.placeholder}
            .hideBreadcrumbs=${this.hideBreadcrumbs}
            .breadcrumbs=${this.breadcrumbs}
            @change=${this._handleInput}
            @setParent=${e=>this.setParent(e.detail.parent)}
            @close=${this.close}
          >
          </ninja-header>
          <div class="modal-body">
            <div class="actions-list" part="actions-list">${s}</div>
          </div>
          <slot name="footer"> ${xi} </slot>
        </div>
      </div>
    `}get _selectedIndex(){return this._selected?this._actionMatches.indexOf(this._selected):-1}_actionSelected(e){var t;if(this.dispatchEvent(new CustomEvent("selected",{detail:{search:this._search,action:e},bubbles:!0,composed:!0})),e){if(e.children&&(null===(t=e.children)||void 0===t?void 0:t.length)>0&&(this._currentRoot=e.id,this._search=""),this._headerRef.value.setSearch(""),this._headerRef.value.focusSearch(),e.handler){const t=e.handler(e);(null==t?void 0:t.keepOpen)||this.close()}this._bump=!0}}async _handleInput(e){this._search=e.detail.search,await this.updateComplete,this.dispatchEvent(new CustomEvent("change",{detail:{search:this._search,actions:this._actionMatches},bubbles:!0,composed:!0}))}_overlayClick(e){var t;(null===(t=e.target)||void 0===t?void 0:t.classList.contains("modal"))&&this.close()}};Oi.styles=[Pi],ji([he({type:String})],Oi.prototype,"placeholder",void 0),ji([he({type:Boolean})],Oi.prototype,"disableHotkeys",void 0),ji([he({type:Boolean})],Oi.prototype,"hideBreadcrumbs",void 0),ji([he()],Oi.prototype,"openHotkey",void 0),ji([he()],Oi.prototype,"navigationUpHotkey",void 0),ji([he()],Oi.prototype,"navigationDownHotkey",void 0),ji([he()],Oi.prototype,"closeHotkey",void 0),ji([he()],Oi.prototype,"goBackHotkey",void 0),ji([he()],Oi.prototype,"selectHotkey",void 0),ji([he({type:Boolean})],Oi.prototype,"hotKeysJoinedView",void 0),ji([he({type:Boolean})],Oi.prototype,"noAutoLoadMdIcons",void 0),ji([he({type:Array,hasChanged:()=>!0})],Oi.prototype,"data",void 0),ji([de()],Oi.prototype,"visible",void 0),ji([de()],Oi.prototype,"_bump",void 0),ji([de()],Oi.prototype,"_actionMatches",void 0),ji([de()],Oi.prototype,"_search",void 0),ji([de()],Oi.prototype,"_currentRoot",void 0),ji([de()],Oi.prototype,"_flatData",void 0),ji([de()],Oi.prototype,"breadcrumbs",null),ji([de()],Oi.prototype,"_selected",void 0),Oi=ji([le("ninja-keys")],Oi)},553:function(module,__webpack_exports__,__webpack_require__){"use strict";__webpack_require__.r(__webpack_exports__);var react__WEBPACK_IMPORTED_MODULE_0__=__webpack_require__(1),react__WEBPACK_IMPORTED_MODULE_0___default=__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__),_components_other_FefferyShortcutPanel_react__WEBPACK_IMPORTED_MODULE_1__=__webpack_require__(275),ninja_keys__WEBPACK_IMPORTED_MODULE_2__=__webpack_require__(1141),lodash__WEBPACK_IMPORTED_MODULE_3__=__webpack_require__(16),lodash__WEBPACK_IMPORTED_MODULE_3___default=__webpack_require__.n(lodash__WEBPACK_IMPORTED_MODULE_3__),_components_styleControl_FefferyStyle_react__WEBPACK_IMPORTED_MODULE_4__=__webpack_require__(108),_components_utils__WEBPACK_IMPORTED_MODULE_5__=__webpack_require__(3);function _typeof(e){return(_typeof="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}function ownKeys(e,t){var i=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),i.push.apply(i,n)}return i}function _objectSpread(e){for(var t=1;t<arguments.length;t++){var i=null!=arguments[t]?arguments[t]:{};t%2?ownKeys(Object(i),!0).forEach((function(t){_defineProperty(e,t,i[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(i)):ownKeys(Object(i)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(i,t))}))}return e}function _defineProperty(e,t,i){return(t=_toPropertyKey(t))in e?Object.defineProperty(e,t,{value:i,enumerable:!0,configurable:!0,writable:!0}):e[t]=i,e}function _toPropertyKey(e){var t=_toPrimitive(e,"string");return"symbol"==_typeof(t)?t:t+""}function _toPrimitive(e,t){if("object"!=_typeof(e)||!e)return e;var i=e[Symbol.toPrimitive];if(void 0!==i){var n=i.call(e,t||"default");if("object"!=_typeof(n))return n;throw new TypeError("@@toPrimitive must return a primitive value.")}return("string"===t?String:Number)(e)}var footerHtmlEn=react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("div",{class:"modal-footer",slot:"footer"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{class:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"enter"),"to select"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("svg",{xmlns:"http://www.w3.org/2000/svg",className:"ninja-examplekey",viewBox:"0 0 24 24"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M0 0h24v24H0V0z",fill:"none"}),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z"})),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("svg",{xmlns:"http://www.w3.org/2000/svg",className:"ninja-examplekey",viewBox:"0 0 24 24"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M0 0h24v24H0V0z",fill:"none"}),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z"})),"to navigate"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"esc"),"to close"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"backspace"),"move to parent")),footerHtmlZh=react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("div",{className:"modal-footer",slot:"footer"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"enter"),"选择"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("svg",{xmlns:"http://www.w3.org/2000/svg",className:"ninja-examplekey",viewBox:"0 0 24 24"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M0 0h24v24H0V0z",fill:"none"}),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z"})),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("svg",{xmlns:"http://www.w3.org/2000/svg",className:"ninja-examplekey",viewBox:"0 0 24 24"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M0 0h24v24H0V0z",fill:"none"}),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("path",{d:"M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z"})),"上下切换"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"esc"),"关闭面板"),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"help"},react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("span",{className:"ninja-examplekey esc"},"backspace"),"回到上一级")),locale2footer=new Map([["en",footerHtmlEn],["zh",footerHtmlZh]]),locale2placeholder=new Map([["en","Type a command or search..."],["zh","输入指令或进行搜索..."]]),FefferyShortcutPanel=function FefferyShortcutPanel(_ref){var id=_ref.id,data=_ref.data,placeholder=_ref.placeholder,openHotkey=_ref.openHotkey,theme=_ref.theme,locale=_ref.locale,open=_ref.open,close=_ref.close,panelStyles=_ref.panelStyles,setProps=_ref.setProps;data=data.map((function(e){return Object(lodash__WEBPACK_IMPORTED_MODULE_3__.isString)(e.handler)||e.hasOwnProperty("children")?e:_objectSpread(_objectSpread({},e),{handler:function(){setProps({triggeredHotkey:{id:e.id,timestamp:Date.parse(new Date)}})}})}));var ninjaKeys=Object(react__WEBPACK_IMPORTED_MODULE_0__.useRef)(null);return Object(react__WEBPACK_IMPORTED_MODULE_0__.useEffect)((function(){ninjaKeys.current&&ninjaKeys.current.addEventListener("change",(function(e){setProps({searchValue:e.detail.search})}))}),[]),Object(react__WEBPACK_IMPORTED_MODULE_0__.useEffect)((function(){ninjaKeys.current&&(ninjaKeys.current.data=data.map((function(item){return Object(lodash__WEBPACK_IMPORTED_MODULE_3__.isString)(item.handler)?_objectSpread(_objectSpread({},item),{handler:eval(item.handler)}):item})))}),[data]),Object(react__WEBPACK_IMPORTED_MODULE_0__.useEffect)((function(){ninjaKeys.current&&open&&(ninjaKeys.current.open(),setProps({open:!1}))}),[open]),Object(react__WEBPACK_IMPORTED_MODULE_0__.useEffect)((function(){ninjaKeys.current&&close&&(ninjaKeys.current.close(),setProps({close:!1}))}),[close]),panelStyles=_objectSpread(_objectSpread({},{width:"640px",overflowBackground:"rgba(255, 255, 255, 0.5)",textColor:"rgb(60, 65, 73)",fontSize:"16px",top:"20%",accentColor:"rgb(110, 94, 210)",secondaryBackgroundColor:"rgb(239, 241, 244)",secondaryTextColor:"rgb(107, 111, 118)",selectedBackground:"rgb(248, 249, 251)",actionsHeight:"300px",groupTextColor:"rgb(144, 149, 157)",zIndex:1}),panelStyles),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement(react__WEBPACK_IMPORTED_MODULE_0___default.a.Fragment,null,react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement(_components_styleControl_FefferyStyle_react__WEBPACK_IMPORTED_MODULE_4__.a,{rawStyle:"\nninja-keys {\n    --ninja-width: ".concat(panelStyles.width,";\n    --ninja-overflow-background: ").concat(panelStyles.overflowBackground,";\n    --ninja-text-color: ").concat(panelStyles.textColor,";\n    --ninja-font-size: ").concat(panelStyles.fontSize,";\n    --ninja-top: ").concat(panelStyles.top,";\n    --ninja-accent-color: ").concat(panelStyles.accentColor,";\n    --ninja-secondary-background-color: ").concat(panelStyles.secondaryBackgroundColor,";\n    --ninja-secondary-text-color: ").concat(panelStyles.secondaryTextColor,";\n    --ninja-selected-background: ").concat(panelStyles.selectedBackground,";\n    --ninja-actions-height: ").concat(panelStyles.actionsHeight,";\n    --ninja-group-text-color: ").concat(panelStyles.groupTextColor,";\n    --ninja-z-index: ").concat(panelStyles.zIndex,";\n}\n")}),react__WEBPACK_IMPORTED_MODULE_0___default.a.createElement("ninja-keys",{id:id,class:theme,ref:ninjaKeys,placeholder:placeholder||locale2placeholder.get(locale),openHotkey:openHotkey,hotKeysJoinedView:!0,hideBreadcrumbs:!0,"data-dash-is-loading":Object(_components_utils__WEBPACK_IMPORTED_MODULE_5__.d)()},locale2footer.get(locale)))};__webpack_exports__.default=FefferyShortcutPanel,FefferyShortcutPanel.defaultProps=_components_other_FefferyShortcutPanel_react__WEBPACK_IMPORTED_MODULE_1__.b,FefferyShortcutPanel.propTypes=_components_other_FefferyShortcutPanel_react__WEBPACK_IMPORTED_MODULE_1__.c}}]);
//# sourceMappingURL=async-feffery_shortcut_panel.js.map
//# sourceMappingURL=async-feffery_shortcut_panel.js.map