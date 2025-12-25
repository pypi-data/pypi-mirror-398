import base64
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from ..constantes import RetourClientConstantes
from ..forms import ReponseBugForm, RetourClientForm
from ..http_utils import safe_get_json, safe_post_json
from ..models import RetourClient
from ..services.statuts_bug import RetourBugService
from ..utils import AnymailModuleRetourUtils

logger = logging.getLogger(__name__)


class RetourClientView(View):
    def get(self, request):
        form_bug = RetourClientForm()
        return render(request, 'retour_client.html', {'form_bug': form_bug})

    def post(self, request):
        form_bug = RetourClientForm(request.POST, request.FILES)
        if form_bug.is_valid():
            try:
                with transaction.atomic():
                    retour_client = form_bug.save(commit=False)
                    retour_client.utilisateur = request.user.email if request.user.is_authenticated else RetourClientConstantes.INCONNU
                    retour_client.navigateur = request.META['HTTP_USER_AGENT'][:100]
                    retour_client.lien_url = request.POST.get('lien_url')

                    # Traitement de l'image (capture d'écran)
                    image_data = request.POST.get('image')
                    if image_data:
                        format, imgstr = image_data.split(';base64,')
                        ext = format.split('/')[-1]
                        retour_client.image = ContentFile(base64.b64decode(imgstr),
                                                          name=f'screenshot_{datetime.now().strftime("%Y%m%d%H%M%S")}.{ext}')

                    retour_client.save()

                    # Vérifier si DATE_FIN_GARANTIE est définie
                    date_fin_garantie = getattr(settings, 'DATE_FIN_GARANTIE', None)
                    if date_fin_garantie:
                        date_fin = datetime.strptime(date_fin_garantie, '%Y-%m-%d').date()
                        aujourd_hui = timezone.now().date()
                        hors_garantie = date_fin < aujourd_hui
                    else:
                        hors_garantie = False

                    if settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.PRODUCTION and hors_garantie:
                        body_html = AnymailModuleRetourUtils.render_template(
                            '../../retour_client/templates/mails/nouveau-ticket-client.tpl',
                            {"retour_client": retour_client})

                        # Récupération des infos par API Lucy :
                        # URL de l'API
                        siren = settings.SIREN_CLIENT

                        url = f"https://app.lucy-crm.fr/api/credit-client/{siren}"
                        data, err = safe_get_json(url, timeout=(2, 5))
                        if data:
                            collaborateur_associe = data.get("collaborateur_associe") or 'maxence@revolucy.fr'
                        else:
                            logger.error(f"[Lucy API] collaborateur_associe par défaut (erreur: {err})")
                            collaborateur_associe = 'maxence@revolucy.fr'

                        AnymailModuleRetourUtils.send_mail(
                            f"Nouveau Ticket Client #{retour_client.pk} ({settings.EMAIL_CLIENT_RETOUR})",
                            [collaborateur_associe], body_html=body_html)

                    return JsonResponse({'success': True})

            except Exception as e:
                logger.error(f'Une erreur ({type(e).__name__}) est survenue à la création du ticket : {e}')
                return JsonResponse({'success': False, 'errors': str(e)})
        else:
            return JsonResponse({'success': False, 'errors': form_bug.errors.as_json()})


class PipelineRetourClientView(LoginRequiredMixin, TemplateView):
    template_name = 'pipeline-retour-client.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        # Contexte pour formulaire de recherche
        current_user = self.request.user
        if current_user.is_admin_revo:
            bugs = RetourClient.objects.exclude(
                Q(statut=RetourClientConstantes.VALIDE) | Q(statut=RetourClientConstantes.TRAITE) | Q(
                    statut=RetourClientConstantes.V2))
        else:
            bugs = RetourClient.objects.filter(statut=RetourClientConstantes.TRAITE)
        grouped_bugs = {}

        for bug in bugs:
            if bug.lien_url not in grouped_bugs:
                grouped_bugs[bug.lien_url] = []
            grouped_bugs[bug.lien_url].append(bug)

        context['grouped_bugs'] = grouped_bugs
        context['search_users'] = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        context['search_statuts'] = RetourClientConstantes.statut
        context['search_types'] = RetourClientConstantes.type
        context['search_priorite'] = RetourClientConstantes.priorite

        # DATA
        bugs_data = RetourClient.objects.all()
        context['nb_bug'] = bugs_data.filter(type=RetourClientConstantes.BUG).count()
        context['nb_question'] = bugs_data.filter(type=RetourClientConstantes.QUESTION).count()
        context['nb_v1'] = bugs_data.filter(type=RetourClientConstantes.AMELIORATION).exclude(
            statut=RetourClientConstantes.V2).count()
        context['nb_v2'] = bugs_data.filter(statut=RetourClientConstantes.V2).count()
        context['nb_non_classe'] = bugs_data.filter(type=RetourClientConstantes.NON_CLASSE).count()

        return context


class KanbanRetourClientView(LoginRequiredMixin, TemplateView):
    template_name = 'kanban-retour-client.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        bugs = RetourClient.objects.exclude(statut=RetourClientConstantes.VALIDE)
        total = RetourClient.objects.all().count()

        kanban_rows = []
        for key, label in RetourClientConstantes.statut_client:
            qs = bugs.filter(statut=key)
            count = qs.count()
            pct = (count * 100 / total) if total else 0
            kanban_rows.append({
                "label": label,
                "items": qs,
                "count": count,
                "pct": pct,
            })

        context.update({
            "kanban_rows": kanban_rows,
            "kanban_total": total,
        })
        return context


class RefusValidationBugLink(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_refus_validation_bug(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content_inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_types': search_types,
            'search_statuts': search_statuts,
            'search_priorite': search_priorite
        }


class RetourClientItemView(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get_template_names(self):
        if self.request.GET.get("modal") == "1":
            return ["formulaire_edition_modal.html"]
        return ["detail-retour-client.html"]

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('HX-Request'):
            tpl = self.get_template_names()[0]
            html = render_to_string(tpl, context, request=request)
            return HttpResponse(html)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        bug_id = kwargs.get('pk')
        bug = get_object_or_404(RetourClient, pk=bug_id)
        context['bug'] = bug
        context['display_status'] = bug.display_status_for(self.request.user)
        context['form'] = ReponseBugForm(current_user=self.request.user)

        if self.request.GET.get('modal') == '1':
            context['target_id'] = '#modal-edit-content-inner'
            context['is_modal'] = True

        # Contexte pour formulaire de recherche
        current_user = self.request.user
        if current_user.is_admin_revo:
            bugs = RetourClient.objects.exclude(
                Q(statut=RetourClientConstantes.VALIDE) | Q(statut=RetourClientConstantes.TRAITE) | Q(
                    statut=RetourClientConstantes.V2))
        else:
            bugs = RetourClient.objects.exclude(
                Q(statut=RetourClientConstantes.TRAITE) | Q(statut=RetourClientConstantes.V2))
        grouped_bugs = {}

        for bug in bugs:
            if bug.lien_url not in grouped_bugs:
                grouped_bugs[bug.lien_url] = []
            grouped_bugs[bug.lien_url].append(bug)

        context['grouped_bugs'] = grouped_bugs
        context['search_users'] = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        context['search_types'] = RetourClientConstantes.type
        context['search_statuts'] = RetourClientConstantes.statut
        context['search_priorite'] = RetourClientConstantes.priorite

        return context

    def post(self, request, *args, **kwargs):
        bug_id = kwargs.get('pk')
        bug = get_object_or_404(RetourClient, pk=bug_id)
        form = ReponseBugForm(request.POST, files=request.FILES, current_user=request.user)
        if form.is_valid():
            reponse_bug = form.save(commit=False)
            reponse_bug.retour_client = bug
            reponse_bug.save()

            # Traitement du ticket en production hors période de garantie
            if reponse_bug.temps_passe and reponse_bug.temps_passe > 0 and settings.ENVIRONNEMENT == RetourClientConstantes.Environnement.PRODUCTION:
                # URL de l'API
                siren = settings.SIREN_CLIENT

                url = "https://app.lucy-crm.fr/api/resolution-ticket"
                payload = {
                    "temps_passe": float(reponse_bug.temps_passe) if isinstance(reponse_bug.temps_passe,
                                                                                Decimal) else reponse_bug.temps_passe,
                    "siren_client": siren,
                    "entreprise": "1",
                    "num_ticket": reponse_bug.retour_client.pk
                }
                headers = {"Content-Type": "application/json"}

                resp, err = safe_post_json(url, payload, headers=headers, timeout=(2, 5))
                if not resp or resp.status_code != 201:
                    extra = f"err={err}" if err else f"HTTP {resp.status_code}: {getattr(resp, 'text', '')}"
                    logger.error(f"[Lucy API] Échec résolution-ticket, fallback sans bloquer: {extra}")

                # Envoi de la notification mail au client
                body_html = AnymailModuleRetourUtils.render_template(
                    '../../retour_client/templates/mails/reponse-ticket-client.tpl', {"reponse_bug": reponse_bug})

                AnymailModuleRetourUtils.send_mail(f"Réponse à votre ticket #{reponse_bug.pk}", [settings.EMAIL_CLIENT_RETOUR],
                                       body_html=body_html)

            if request.headers.get('HX-Request'):
                context = self.get_context_data(**kwargs)
                tpl = self.get_template_names()[0]
                html = render_to_string(tpl, context, request=request)
                return HttpResponse(html)
            return redirect('retour_client:item_retour', pk=bug_id)
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class ChangementStatutBugLink(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_changement_statut_bug(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content-inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_statuts': search_statuts,
            'search_types': search_types,
            'search_priorite': search_priorite
        }


class FilteredRetourClientListView(LoginRequiredMixin, TemplateView):
    template_name = 'liste-retour-client.html'

    def get_queryset(self):
        queryset = RetourClient.objects.all()
        recherche_txt = self.request.GET.get('recherche_txt')
        statut = self.request.GET.get('statut')
        type = self.request.GET.get('type')
        utilisateur = self.request.GET.get('utilisateur')
        priorite = self.request.GET.get('priorite')

        filters = Q()  # Initialise un filtre vide

        if recherche_txt:
            filters &= Q(titre__icontains=recherche_txt)
        if statut:
            filters &= Q(statut=statut)
        if type:
            filters &= Q(type=type)
        if utilisateur:
            filters &= Q(utilisateur=utilisateur)
        if priorite:
            filters &= Q(priorite=priorite)

        return queryset.filter(filters)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bugs = self.get_queryset()
        grouped_bugs = {}

        for bug in bugs:
            if bug.lien_url not in grouped_bugs:
                grouped_bugs[bug.lien_url] = []
            grouped_bugs[bug.lien_url].append(bug)

        context['grouped_bugs'] = grouped_bugs
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('HX-Request'):
            html = render_to_string(self.template_name, context, request=self.request)
            return HttpResponse(html)
        return super().render_to_response(context, **response_kwargs)


# BTN Gestion de projet

class ChangementStatutV2Link(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_changement_statut_v2(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content-inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_statuts': search_statuts,
            'search_types': search_types,
            'search_priorite': search_priorite
        }


class ChangementTypeV1Link(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_changement_type_v1(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content-inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_statuts': search_statuts,
            'search_types': search_types,
            'search_priorite': search_priorite
        }


class ChangementTypeQuestionLink(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_changement_type_question(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content-inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_statuts': search_statuts,
            'search_types': search_types,
            'search_priorite': search_priorite
        }


class ChangementTypeBugLink(LoginRequiredMixin, TemplateView):
    template_name = 'detail-retour-client.html'

    def get(self, request, *args, **kwargs):
        bug_id = kwargs.get('id_bug')
        bug = get_object_or_404(RetourClient, pk=bug_id)

        # Process de changement des statuts
        RetourBugService.lien_changement_type_bug(request, bug)

        if request.headers.get('HX-Request'):
            context = self.get_context_data(bug)
            if request.GET.get('modal') == '1':
                context['target_id'] = '#modal-edit-content-inner'
                context['is_modal'] = True
            html = render_to_string(self.template_name, context, request=request)
            return HttpResponse(html)
        return redirect('retour_client:item_retour', pk=bug_id)

    def get_context_data(self, bug):
        form = ReponseBugForm(current_user=self.request.user)
        # Contexte pour formulaire de recherche
        bugs = RetourClient.objects.all()
        search_users = RetourClient.objects.values_list('utilisateur', flat=True).distinct()
        search_statuts = RetourClientConstantes.statut
        search_types = RetourClientConstantes.type
        search_priorite = RetourClientConstantes.priorite

        return {
            'bug': bug,
            'display_status': bug.display_status_for(self.request.user),
            'form': form,

            'bugs': bugs,
            'search_users': search_users,
            'search_statuts': search_statuts,
            'search_types': search_types,
            'search_priorite': search_priorite
        }


@require_POST
def update_statut_kanban(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        retour_id = data.get('id')
        new_statut = data.get('new_statut')

        valid_keys = {k for k, _ in RetourClientConstantes.statut}
        if new_statut in valid_keys:
            new_key = new_statut
        else:
            label_to_key = {label: key for key, label in RetourClientConstantes.statut_client}
            new_key = label_to_key.get(new_statut)

        if not new_key:
            return JsonResponse({"ok": False, "error": "Statut invalide"}, status=400)

        with transaction.atomic():
            bug = RetourClient.objects.select_for_update().get(pk=retour_id)
            bug.statut = new_key
            bug.save(update_fields=['statut'])

        return JsonResponse({"ok": True, "id": bug.pk, "statut": bug.statut})
    except RetourClient.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Ticket introuvable"}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


class CockpitView(LoginRequiredMixin, TemplateView):
    template_name = 'cockpit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # Tous les tickets
        all_tickets = RetourClient.objects.all()
        total_tickets = all_tickets.count()

        # KPIs généraux
        context['total_tickets'] = total_tickets
        context['tickets_en_attente'] = all_tickets.filter(statut=RetourClientConstantes.EN_ATTENTE).count()
        context['tickets_en_cours'] = all_tickets.filter(statut=RetourClientConstantes.EN_TRAITEMENT).count()
        context['tickets_traites'] = all_tickets.filter(statut=RetourClientConstantes.TRAITE).count()
        context['tickets_valides'] = all_tickets.filter(statut=RetourClientConstantes.VALIDE).count()
        context['tickets_v2'] = all_tickets.filter(statut=RetourClientConstantes.V2).count()

        # Tickets critiques non résolus
        context['tickets_critiques'] = all_tickets.filter(
            priorite=RetourClientConstantes.CRITIQUE
        ).exclude(
            statut__in=[RetourClientConstantes.VALIDE, RetourClientConstantes.TRAITE]
        ).count()

        # Répartition par type
        context['nb_bugs'] = all_tickets.filter(type=RetourClientConstantes.BUG).count()
        context['nb_questions'] = all_tickets.filter(type=RetourClientConstantes.QUESTION).count()
        context['nb_ameliorations'] = all_tickets.filter(type=RetourClientConstantes.AMELIORATION).count()
        context['nb_non_classes'] = all_tickets.filter(type=RetourClientConstantes.NON_CLASSE).count()

        # Répartition par priorité
        context['nb_critique'] = all_tickets.filter(priorite=RetourClientConstantes.CRITIQUE).count()
        context['nb_normal'] = all_tickets.filter(priorite=RetourClientConstantes.NORMAL).count()
        context['nb_non_urgent'] = all_tickets.filter(priorite=RetourClientConstantes.NON_URGENT).count()

        # Tickets créés cette semaine / ce mois
        debut_semaine = now - timedelta(days=now.weekday())
        debut_mois = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        context['tickets_cette_semaine'] = all_tickets.filter(date_ajout__gte=debut_semaine).count()
        context['tickets_ce_mois'] = all_tickets.filter(date_ajout__gte=debut_mois).count()

        # Taux de résolution (validé / total)
        if total_tickets > 0:
            context['taux_resolution'] = round(
                (context['tickets_valides'] / total_tickets) * 100, 1
            )
        else:
            context['taux_resolution'] = 0

        # Évolution mensuelle des tickets (12 derniers mois)
        # Utilisation d'une approche Python pour éviter les problèmes de timezone MySQL
        mois_labels = []
        mois_data = []
        mois_resolus_data = []

        for i in range(11, -1, -1):
            # Calcul du premier jour du mois
            mois_date = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            # Calcul du dernier jour du mois
            if mois_date.month == 12:
                fin_mois = mois_date.replace(year=mois_date.year + 1, month=1, day=1)
            else:
                fin_mois = mois_date.replace(month=mois_date.month + 1, day=1)

            # Tickets créés ce mois
            nb_tickets = all_tickets.filter(
                date_ajout__gte=mois_date,
                date_ajout__lt=fin_mois
            ).count()

            # Tickets validés ce mois
            nb_resolus = all_tickets.filter(
                date_ajout__gte=mois_date,
                date_ajout__lt=fin_mois,
                statut=RetourClientConstantes.VALIDE
            ).count()

            mois_labels.append(mois_date.strftime('%b %Y'))
            mois_data.append(nb_tickets)
            mois_resolus_data.append(nb_resolus)

        context['mois_labels'] = json.dumps(mois_labels)
        context['mois_data'] = json.dumps(mois_data)
        context['mois_resolus_data'] = json.dumps(mois_resolus_data)

        # Top 5 des pages avec le plus de tickets
        top_pages = (
            all_tickets.values('lien_url')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        context['top_pages'] = list(top_pages)

        # Top 5 des utilisateurs avec le plus de tickets
        top_users = (
            all_tickets.values('utilisateur')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )
        context['top_users'] = list(top_users)

        # Temps total passé (depuis ReponseBug)
        from ..models import ReponseBug
        temps_total = ReponseBug.objects.aggregate(total=Sum('temps_passe'))['total'] or 0
        context['temps_total_passe'] = float(temps_total)

        # Données pour graphique statut (doughnut)
        context['statut_data'] = json.dumps([
            context['tickets_en_attente'],
            context['tickets_en_cours'],
            context['tickets_traites'],
            context['tickets_valides'],
            context['tickets_v2'],
        ])
        context['statut_labels'] = json.dumps([
            'En attente', 'En cours', 'Traité', 'Validé', 'V2'
        ])

        # Données pour graphique type (doughnut)
        context['type_data'] = json.dumps([
            context['nb_bugs'],
            context['nb_questions'],
            context['nb_ameliorations'],
            context['nb_non_classes'],
        ])
        context['type_labels'] = json.dumps([
            'Bug', 'Question', 'Amélioration', 'Non classé'
        ])

        # Données pour graphique priorité (bar)
        context['priorite_data'] = json.dumps([
            context['nb_critique'],
            context['nb_normal'],
            context['nb_non_urgent'],
        ])
        context['priorite_labels'] = json.dumps([
            'Critique', 'Normal', 'Non urgent'
        ])

        return context
