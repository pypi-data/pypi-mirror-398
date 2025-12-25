from __future__ import annotations

from django.db.models import QuerySet

from unicrm.models import Contact, MailingList, Segment, Communication


def audience_queryset(
    segment: Segment | None,
    mailing_list: MailingList | None,
    communication: Communication | None = None,
) -> QuerySet[Contact]:
    """
    Returns the contacts matching the provided segment and optional mailing list.
    - If no segment is provided, returns an empty queryset.
    - When mailing list is provided, limits to active subscriptions on that list.
    - Always excludes unsubscribe-all contacts.
    """
    if not segment:
        return Contact.objects.none()

    prev_comm = communication.follow_up_for if communication else None
    base_qs = Contact.objects.all()
    if prev_comm:
        base_qs = base_qs.filter(communications__communication=prev_comm)
    qs = segment.apply(base_qs, previous_comm=prev_comm)
    apply_mailing_list = mailing_list if mailing_list and not prev_comm else None
    if apply_mailing_list:
        qs = qs.filter(
            subscriptions__mailing_list=apply_mailing_list,
            subscriptions__unsubscribed_at__isnull=True,
        )
    qs = qs.exclude(unsubscribe_all_entries__isnull=False).distinct()
    return qs


def audience_size_and_sample(
    segment: Segment | None,
    mailing_list: MailingList | None,
    communication: Communication | None = None,
    *,
    limit: int = 10,
    apply_guards: bool = False,
) -> tuple[int, list[dict]]:
    """
    Returns (count, sample list) for the given audience using only segment + mailing list.
    Anti-spam guards are intentionally not applied here; they are enforced at send time
    so that previews/reporting reflect the full intended audience.
    """
    qs = audience_queryset(segment, mailing_list, communication=communication).select_related('company').order_by('pk')
    contacts: list[Contact] = list(qs)

    total = len(contacts)
    sample = [
        {
            'id': c.pk,
            'email': c.email,
            'first_name': c.first_name,
            'last_name': c.last_name,
            'company': c.company.name if c.company else '',
        }
        for c in contacts[:limit]
    ]
    return total, sample
