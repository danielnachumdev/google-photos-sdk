from typing import Optional
from .....utils import Printable
from .date_filter import DateFilter
from .content_filter import ContentFilter
from .feature_filter import FeatureFilter
from .media_type_filter import MediaTypeFilter


class SearchFilter(Printable):
    """Filters that can be applied to a media item search. 
    If multiple filter options are specified, they're treated as AND with each other.

    Args:
        dateFilter (Optional[DateFilter], optional): Filters the media items based on their creation date. 
            Defaults to None.
        contentFilter (Optional[ContentFilter], optional): Filters the media items based on their content. 
            Defaults to None.
        mediaTypeFilter (Optional[MediaTypeFilter], optional): Filters the media items based on the type of media. 
            Defaults to None.
        featureFilter (Optional[FeatureFilter], optional): Filters the media items based on their features. 
            Defaults to None.
        includeArchivedMedia (bool, optional): If set, the results include media items that the user has archived. 
            Defaults to false (archived media items aren't included). Defaults to False.
        excludeNonAppCreatedData (bool, optional): f set, the results exclude media items that 
            were not created by this app. 
            Defaults to false (all media items are returned). 
            This field is ignored if the photoslibrary.readonly.appcreateddata scope is used. Defaults to False.
    """

    def __init__(self,
                 dateFilter: Optional[DateFilter] = None,
                 contentFilter: Optional[ContentFilter] = None,
                 mediaTypeFilter: Optional[MediaTypeFilter] = None,
                 featureFilter: Optional[FeatureFilter] = None,
                 includeArchivedMedia: bool = False,
                 excludeNonAppCreatedData: bool = False
                 ) -> None:
        """_summary_

        Args:
            dateFilter (Optional[DateFilter], optional): Filters the media items based on their creation date.
                Defaults to None.
            contentFilter (Optional[ContentFilter], optional): Filters the media items based on their content.
                Defaults to None.
            mediaTypeFilter (Optional[MediaTypeFilter], optional): Filters the media items based on the type of media.
                Defaults to None.
            featureFilter (Optional[FeatureFilter], optional): Filters the media items based on their features.
                Defaults to None.
            includeArchivedMedia (bool, optional): If set, the results include media items that the
                user has archived. 
                Defaults to false (archived media items aren't included).. Defaults to False.
            excludeNonAppCreatedData (bool, optional): f set, the results exclude media items that were not 
                created by this app. Defaults to false (all media items are returned). 
                This field is ignored if the photoslibrary.readonly.appcreateddata scope is used.. Defaults to False.
        """
        self.dateFilter = dateFilter
        self.contentFilter = contentFilter
        self.mediaTypeFilter = mediaTypeFilter
        self.featureFilter = featureFilter
        self.includeArchivedMedia = includeArchivedMedia
        self.excludeNonAppCreatedData = excludeNonAppCreatedData
